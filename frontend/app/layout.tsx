// import type { Metadata } from 'next'
// import './globals.css'

// export const metadata: Metadata = {
//   title: 'tier-sense',
//   description: 'Created with v0',
//   generator: 'v0.dev',
// }

// export default function RootLayout({
//   children,
// }: Readonly<{
//   children: React.ReactNode
// }>) {
//   return (
//     <html lang="en">
//       <body>{children}</body>
//     </html>
//   )
// }

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TierSense',
  description: 'LLM-powered file access tiering advisor',
  openGraph: {
    title: 'TierSense',
    description: 'Analyze and optimize file storage with LLM-backed intelligence.',
    // url: 'https://tiersense.example.com', Replace with your actual deployment URL
    siteName: 'TierSense',
    images: [
      {
        url: '/og-image.png', // Put this image inside /public folder
        width: 1200,
        height: 630,
        alt: 'TierSense Dashboard Preview',
      },
    ],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TierSense',
    description: 'AI-powered storage tiering recommendations based on file access patterns.',
    images: ['/og-image.png'],
    creator: '@yourhandle', // Optional — remove or update if needed
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="bg-white text-black">{children}</body>
    </html>
  )
}
