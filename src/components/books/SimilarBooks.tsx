'use client';

import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { findSimilarBooks } from '@/ai/flows/find-similar-books';
import type { Book } from '@/lib/types';

interface SimilarBooksProps {
  book: Book;
}

export default function SimilarBooks({ book }: SimilarBooksProps) {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFindSimilar = async () => {
    setIsLoading(true);
    setError(null);
    setRecommendations([]);
    try {
      const result = await findSimilarBooks({
        title: book.title,
        author: book.author,
        description: book.description,
      });
      setRecommendations(result.recommendations);
    } catch (e) {
      setError('Could not fetch recommendations. Please try again.');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold font-headline">Similar Books</h2>
      <p className="text-muted-foreground mb-4">
        Find books you'll love based on "{book.title}".
      </p>
      <Button onClick={handleFindSimilar} disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Finding...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate with AI
          </>
        )}
      </Button>

      {error && <p className="text-destructive mt-4">{error}</p>}

      {recommendations.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>AI Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 space-y-2">
              {recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
