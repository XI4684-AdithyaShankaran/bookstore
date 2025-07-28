import BookGrid from '@/components/books/BookGrid';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-center font-headline">
        Discover Your Next Read
      </h1>
      <BookGrid />
    </div>
  );
}
