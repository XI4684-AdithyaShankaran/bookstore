import BookGrid from '@/components/books/BookGrid';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export default function Home() {
  return (
    <div>
      <section className="text-center px-4 py-12 md:py-20 lg:py-24 bg-card/50">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold font-headline mb-4">
            Find your next great read.
          </h1>
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-muted-foreground mb-8">
            Explore thousands of books, get AI-powered recommendations, and connect with a community of readers.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
                <Link href="/recommendations">
                    <Sparkles className="mr-2"/>
                    Get AI Recommendations
                </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
                <Link href="/bookshelves">Browse Bookshelves</Link>
            </Button>
          </div>
      </section>

      <div className="container mx-auto px-4 py-12">
        <h2 className="text-3xl font-bold font-headline mb-8">Popular Books</h2>
        <BookGrid />
      </div>
    </div>
  );
}
