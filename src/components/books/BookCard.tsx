import Image from 'next/image';
import Link from 'next/link';
import type { Book } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Star } from 'lucide-react';
import BookActions from './BookActions';

interface BookCardProps {
  book: Book;
}

export default function BookCard({ book }: BookCardProps) {
  return (
    <Card className="overflow-hidden group relative break-inside-avoid-column bg-transparent shadow-none border-none">
       <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <BookActions book={book} />
        </div>
      <Link href={`/book/${book.id}`} aria-label={`View details for ${book.title}`}>
        <CardContent className="p-0">
          <div className="relative">
            <Image
              src={book.coverImage}
              alt={`Cover of ${book.title}`}
              width={400}
              height={600}
              className="w-full h-auto object-cover rounded-md transition-transform duration-300 group-hover:scale-105"
              data-ai-hint="book cover"
            />
             <div className="absolute inset-0 bg-black/20 rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
          <div className="mt-2 text-left">
            <h3 className="font-semibold text-base truncate font-headline">{book.title}</h3>
             <p className="text-sm text-muted-foreground truncate">by {book.author}</p>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
