import { notFound } from 'next/navigation';
import Image from 'next/image';
import { mockBooks } from '@/lib/mock-data';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import BookActions from '@/components/books/BookActions';
import SimilarBooks from '@/components/books/SimilarBooks';
import { Separator } from '@/components/ui/separator';

export async function generateStaticParams() {
  return mockBooks.map((book) => ({
    id: book.id.toString(),
  }));
}

export default function BookDetailPage({ params }: { params: { id: string } }) {
  const book = mockBooks.find((b) => b.id.toString() === params.id);

  if (!book) {
    notFound();
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
        <div className="md:col-span-1">
          <Card className="overflow-hidden sticky top-24 shadow-lg">
            <Image
              src={book.coverImage}
              alt={`Cover of ${book.title}`}
              width={400}
              height={600}
              className="w-full h-auto object-cover"
              data-ai-hint="book cover"
              priority
            />
          </Card>
        </div>

        <div className="md:col-span-2">
          <h1 className="text-4xl md:text-5xl font-bold font-headline">
            {book.title}
          </h1>
          <p className="text-xl text-muted-foreground mt-2">by {book.author}</p>

          <div className="flex items-center gap-4 mt-4">
            <Badge variant="secondary">{book.genre}</Badge>
            <div className="flex items-center">
              <span className="text-accent">★</span>
              <span className="ml-1 font-medium">{book.rating}</span>
            </div>
          </div>
          
          <div className="mt-6">
            <BookActions book={book} direction="row" />
          </div>

          <Separator className="my-8" />
          
          <div>
            <h2 className="text-2xl font-bold font-headline mb-4">Description</h2>
            <p className="text-lg leading-relaxed">{book.description}</p>
          </div>

          <Separator className="my-8" />

          <SimilarBooks book={book} />

        </div>
      </div>
    </div>
  );
}
