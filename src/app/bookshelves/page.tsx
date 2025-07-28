import { BookOpen, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

// Mock data for bookshelves
const bookshelves = [
  {
    id: 1,
    name: 'Sci-Fi Favorites',
    description: 'My all-time favorite science fiction novels.',
    bookCount: 2,
  },
  {
    id: 2,
    name: 'To Read',
    description: 'Books I want to read next.',
    bookCount: 5,
  },
  {
    id: 3,
    name: 'Classic Literature',
    description: 'Essential classics for my collection.',
    bookCount: 3,
  },
];

export default function BookshelvesPage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold font-headline">My Bookshelves</h1>
          <p className="mt-2 text-lg text-muted-foreground">
            Organize your books and get personalized recommendations.
          </p>
        </div>
        <Button className="mt-4 md:mt-0">Create New Bookshelf</Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {bookshelves.map((shelf) => (
          <Card key={shelf.id} className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="text-primary" />
                {shelf.name}
              </CardTitle>
              <CardDescription>{shelf.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="text-sm text-muted-foreground">
                {shelf.bookCount} {shelf.bookCount === 1 ? 'book' : 'books'}
              </p>
            </CardContent>
            <div className="p-6 pt-0">
               <Button variant="outline" className="w-full">
                  <Sparkles className="mr-2 h-4 w-4" />
                  Get Recommendations
                </Button>
            </div>
          </Card>
        ))}
        <Card className="border-dashed flex items-center justify-center min-h-[200px]">
           <Button variant="ghost" className="text-lg">
             + Create New Bookshelf
           </Button>
        </Card>
      </div>
    </div>
  );
}
