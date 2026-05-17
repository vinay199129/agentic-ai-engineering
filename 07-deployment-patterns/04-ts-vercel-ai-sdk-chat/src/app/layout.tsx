export const metadata = {
  title: "Agentic AI Engineering — chat",
  description: "Streams from the FastAPI agent backend.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
