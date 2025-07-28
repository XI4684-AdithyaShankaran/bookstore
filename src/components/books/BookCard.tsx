import Image from 'next/image';
import Link from 'next/link';
import type { Book } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import BookActions from './BookActions';

interface BookCardProps {
  book: Book;
}

export default function BookCard({ book }: BookCardProps) {
  return (
    <Card className="overflow-hidden group relative break-inside-avoid-column">
      <Link href={`/book/${book.id}`} aria-label={`View details for ${book.title}`}>
        <div className="absolute inset-0 bg-black/50 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </Link>
      <div className="absolute top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
         <BookActions book={book} />
      </div>
      <CardContent className="p-0">
        <Image
          src={book.coverImage}
          alt={`Cover of ${book.title}`}
          width={400}
          height={600}
          className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
          data-ai-hint="book cover"
        />
        <div className="p-4">
          <h3 className="font-bold text-lg truncate font-headline">{book.title}</h3>
          <p className="text-sm text-muted-foreground">{book.author}</p>
        </div>
      </CardContent>
    </Card>
  );
}
