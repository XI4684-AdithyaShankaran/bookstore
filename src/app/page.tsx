import BookGrid from '@/components/books/BookGrid';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
       <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-2 font-headline">
          Meghna's Bookshelf
        </h1>
        <div className="h-24 w-full bg-muted-foreground/10 rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground text-sm">[Two hands exchanging a book illustration]</p>
        </div>
      </div>
      <BookGrid />
    </div>
  );
}
