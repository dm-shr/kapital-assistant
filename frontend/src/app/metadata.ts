import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Kapital Assistant',
  description: 'AI-powered interface for exploring financial documentation',
  openGraph: {
    title: 'Kapital Assistant',
    description: 'AI-powered interface for exploring financial documentation',
    images: [
      {
        url: '/opengraph-image.png',
        width: 1200,
        height: 630,
        alt: 'Kapital Assistant',
      },
    ],
    type: 'website',
    url: 'https://kapital-assistant.vercel.app/',
  },
};
