import Image from 'next/image';
import Link from 'next/link';
import type { Book } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Star } from 'lucide-react';

interface BookCardProps {
  book: Book;
}

export default function BookCard({ book }: BookCardProps) {
  return (
    <Card className="overflow-hidden group relative break-inside-avoid-column bg-transparent shadow-none border-none">
      <Link href={`/book/${book.id}`} aria-label={`View details for ${book.title}`}>
        <CardContent className="p-0">
          <Image
            src={book.coverImage}
            alt={`Cover of ${book.title}`}
            width={400}
            height={600}
            className="w-full h-auto object-cover rounded-md"
            data-ai-hint="book cover"
          />
          <div className="mt-2 text-left">
            <h3 className="font-semibold text-base truncate font-headline">{book.title}</h3>
            <div className="flex items-center text-sm text-muted-foreground">
                <Star className="w-4 h-4 mr-1 text-yellow-500 fill-yellow-500" />
                <span>{book.rating}</span>
            </div>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
