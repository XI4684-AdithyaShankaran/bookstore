'use client';

import { ShoppingCart, Heart, BookMarked } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import type { Book } from '@/lib/types';

interface BookActionsProps {
  book: Book;
  direction?: 'row' | 'col';
}

export default function BookActions({ book, direction = 'col' }: BookActionsProps) {
  const { toast } = useToast();

  const handleAction = (action: string) => {
    toast({
      title: `${book.title}`,
      description: `Added to your ${action}. (This is a demo)`,
    });
  };

  const containerClasses = direction === 'col' ? 'flex flex-col space-y-2' : 'flex space-x-2';

  return (
    <div className={containerClasses}>
      <Button
        variant="secondary"
        size="icon"
        onClick={() => handleAction('cart')}
        aria-label="Add to cart"
        className="bg-card/80 hover:bg-card text-card-foreground"
      >
        <ShoppingCart />
      </Button>
      <Button
        variant="secondary"
        size="icon"
        onClick={() => handleAction('wishlist')}
        aria-label="Add to wishlist"
        className="bg-card/80 hover:bg-card text-card-foreground"
      >
        <Heart />
      </Button>
      <Button
        variant="secondary"
        size="icon"
        onClick={() => handleAction('bookshelf')}
        aria-label="Add to bookshelf"
        className="bg-card/80 hover:bg-card text-card-foreground"
      >
        <BookMarked />
      </Button>
    </div>
  );
}
