import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { Navbar } from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'AI Photo Retrieval Discovery Engine | Google Photos Research',
  description: 'AI-assisted failure mode analysis and opportunity discovery platform for Google Photos PMs.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="app-container">
            <Navbar />
            <main className="main-content">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
