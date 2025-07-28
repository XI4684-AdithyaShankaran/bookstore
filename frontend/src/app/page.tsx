import BookGrid from '@/components/books/BookGrid';

export default function Home() {
  return (
    <>
      {/* Optional: Add a hero section or introductory content here */}
      <section className="bg-gray-100 py-12 text-center">
        <h1 className="text-3xl md:text-4xl font-bold">Welcome to the Bookstore!</h1>
        <p className="mt-2 text-gray-600">Find your next favorite book.</p>
      </section>

      <BookGrid />
    </>
  );
}
