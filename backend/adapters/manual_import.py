import csv
import io
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from dateutil import parser as date_parser
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService


class ManualImportError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


class ManualImportAdapter(SourceAdapter):
    """
    Adapter for manually uploaded CSV or JSON datasets.
    Validates schemas, parses heterogeneous date formats, cleans contents,
    and returns standardized RawRecord instances in batches.
    """
    platform_name = "manual_import"
    tos_status = "open"

    REQUIRED_COLUMNS = {"raw_content", "source_url", "source_date", "source_platform"}
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        """
        In manual import, config typically contains 'file_content' (str or bytes)
        and 'file_format' ('csv' or 'json').
        """
        file_content = config.get("file_content")
        file_format = config.get("file_format", "csv").lower()

        if not file_content:
            raise ManualImportError("No file content provided for import.")

        if isinstance(file_content, bytes):
            # Check file size limit
            if len(file_content) > self.MAX_FILE_SIZE_BYTES:
                raise ManualImportError(
                    f"File exceeds maximum allowed size of 100MB ({len(file_content) / (1024*1024):.1f}MB). "
                    "Please split the dataset into smaller batches."
                )
            # Try utf-8-sig first to transparently handle BOM
            try:
                file_content = file_content.decode("utf-8-sig")
            except UnicodeDecodeError:
                file_content = file_content.decode("latin-1")
        elif isinstance(file_content, str):
            if len(file_content.encode("utf-8")) > self.MAX_FILE_SIZE_BYTES:
                raise ManualImportError("File exceeds maximum allowed size of 100MB.")

        if file_format == "json":
            raw_records, _ = self.parse_json(file_content)
        else:
            raw_records, _ = self.parse_csv(file_content)

        return raw_records

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        """
        Normalizes a RawRecord using the PreprocessingService pipeline.
        """
        return PreprocessingService.preprocess_raw_record(raw)

    def parse_csv(self, content: str) -> Tuple[List[RawRecord], List[str]]:
        """
        Parses CSV string content, validates headers, and extracts RawRecords.
        """
        errors = []
        records = []

        # Read header / sample to detect dialect / delimiter
        first_line = content.splitlines()[0] if content.splitlines() else ""
        delimiter = ","
        if "\t" in first_line and "," not in first_line:
            delimiter = "\t"
        elif ";" in first_line and "," not in first_line:
            delimiter = ";"
        elif "|" in first_line and "," not in first_line:
            delimiter = "|"
        else:
            try:
                sample = content[:4096]
                sniffer = csv.Sniffer()
                detected = sniffer.sniff(sample).delimiter
                if detected in [",", "\t", ";", "|"]:
                    delimiter = detected
            except Exception:
                delimiter = ","

        f = io.StringIO(content)
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            raise ManualImportError("CSV file is empty or missing headers.", errors=["File contains no headers."])

        # Normalize field names (strip whitespace and lower-case)
        normalized_headers = {name.strip().lower(): name for name in reader.fieldnames if name}
        missing_columns = self.REQUIRED_COLUMNS - set(normalized_headers.keys())

        if missing_columns:
            err_msg = f"Missing required CSV columns: {', '.join(sorted(missing_columns))}"
            raise ManualImportError(
                err_msg,
                errors=[
                    f"Missing required column '{col}'. Required columns are: {', '.join(sorted(self.REQUIRED_COLUMNS))}"
                    for col in sorted(missing_columns)
                ],
            )

        for row_idx, row in enumerate(reader, start=2):
            try:
                # Map back from normalized header names
                raw_content = row.get(normalized_headers["raw_content"], "").strip()
                if not raw_content:
                    errors.append(f"Row {row_idx}: 'raw_content' is empty.")
                    continue

                source_url = row.get(normalized_headers["source_url"], "").strip() or None
                source_platform = row.get(normalized_headers["source_platform"], "").strip() or "manual_upload"
                
                # Parse date
                raw_date_str = row.get(normalized_headers["source_date"], "").strip()
                source_date = self._parse_date_string(raw_date_str)

                # Optional fields
                author_key = normalized_headers.get("author_handle") or normalized_headers.get("author")
                author_handle = row.get(author_key, "").strip() if author_key else "anonymous_user"

                # Metadata parsing
                metadata = {}
                metadata_key = normalized_headers.get("metadata")
                if metadata_key and row.get(metadata_key):
                    raw_meta = row.get(metadata_key).strip()
                    try:
                        metadata = json.loads(raw_meta)
                    except Exception:
                        metadata = {"raw_metadata_str": raw_meta}

                # Capture any extra columns into metadata
                for orig_header in reader.fieldnames:
                    norm = orig_header.strip().lower()
                    if norm not in ["raw_content", "source_url", "source_date", "source_platform", "author_handle", "author", "metadata"]:
                        val = row.get(orig_header)
                        if val is not None and val.strip():
                            metadata[orig_header.strip()] = val.strip()

                records.append(
                    RawRecord(
                        raw_content=raw_content,
                        source_platform=source_platform,
                        source_url=source_url,
                        source_date=source_date,
                        author_handle=author_handle,
                        collection_method="manual_import",
                        metadata=metadata,
                    )
                )
            except Exception as e:
                errors.append(f"Row {row_idx}: Error parsing row - {str(e)}")

        return records, errors

    def parse_json(self, content: str) -> Tuple[List[RawRecord], List[str]]:
        """
        Parses JSON content (list of objects or object with 'records' key).
        """
        errors = []
        records = []

        try:
            data = json.loads(content)
        except Exception as e:
            raise ManualImportError(f"Invalid JSON format: {str(e)}", errors=[str(e)])

        if isinstance(data, dict):
            if "records" in data and isinstance(data["records"], list):
                items = data["records"]
            elif "items" in data and isinstance(data["items"], list):
                items = data["items"]
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            raise ManualImportError("JSON must contain an array of records or an object with a 'records' list.")

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"Item {idx}: Expected a JSON object, got {type(item).__name__}")
                continue

            # Check required fields
            item_keys = {k.lower(): k for k in item.keys()}
            missing = self.REQUIRED_COLUMNS - set(item_keys.keys())
            if missing:
                errors.append(f"Item {idx}: Missing required keys: {', '.join(sorted(missing))}")
                continue

            raw_content = str(item.get(item_keys["raw_content"], "")).strip()
            if not raw_content:
                errors.append(f"Item {idx}: 'raw_content' is empty.")
                continue

            source_url = str(item.get(item_keys["source_url"], "")).strip() or None
            source_platform = str(item.get(item_keys["source_platform"], "")).strip() or "manual_upload"
            
            raw_date = item.get(item_keys["source_date"])
            source_date = self._parse_date_string(str(raw_date)) if raw_date else None

            author_key = item_keys.get("author_handle") or item_keys.get("author")
            author_handle = str(item.get(author_key, "anonymous_user")).strip() if author_key else "anonymous_user"

            meta = item.get(item_keys.get("metadata", ""), {})
            if not isinstance(meta, dict):
                meta = {"raw_metadata": meta}

            records.append(
                RawRecord(
                    raw_content=raw_content,
                    source_platform=source_platform,
                    source_url=source_url,
                    source_date=source_date,
                    author_handle=author_handle,
                    collection_method="manual_import",
                    metadata=meta,
                )
            )

        if not records and errors:
            raise ManualImportError("No valid records found in JSON file.", errors=errors)

        return records, errors

    @staticmethod
    def _parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parses various standard and non-standard date string representations into UTC datetime.
        """
        if not date_str or not date_str.strip():
            return None
        clean_str = date_str.strip()
        try:
            dt = date_parser.parse(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
