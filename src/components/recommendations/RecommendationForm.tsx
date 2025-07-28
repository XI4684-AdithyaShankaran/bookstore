'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sparkles, Loader2 } from 'lucide-react';

import {
  recommendBooksFromPrompt,
  type RecommendBooksFromPromptOutput,
} from '@/ai/flows/recommend-books-from-prompt';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';

const formSchema = z.object({
  prompt: z.string().min(10, {
    message: 'Prompt must be at least 10 characters.',
  }),
});

export default function RecommendationForm() {
  const [recommendations, setRecommendations] = useState<RecommendBooksFromPromptOutput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      prompt: '',
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    setError(null);
    setRecommendations(null);
    try {
      const result = await recommendBooksFromPrompt(values);
      setRecommendations(result);
    } catch (e) {
      setError('Could not fetch recommendations. Please try again.');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }
  
  return (
    <div>
      <Card>
        <CardContent className="pt-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="prompt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Your book prompt</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="e.g., a fast-paced sci-fi thriller with a strong female protagonist"
                        className="resize-none"
                        rows={4}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" disabled={isLoading}>
                 {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Recommendations
                  </>
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
      
      {error && <p className="text-destructive mt-4 text-center">{error}</p>}
      
      {recommendations && (
        <div className="mt-8 space-y-4">
            <h2 className="text-2xl font-bold text-center font-headline">Here are your recommendations!</h2>
            {recommendations.bookRecommendations.map((book, index) => (
                <Card key={index}>
                    <CardHeader>
                        <CardTitle>{book.title}</CardTitle>
                        <CardDescription>{book.author}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p>{book.description}</p>
                    </CardContent>
                </Card>
            ))}
        </div>
      )}
    </div>
  );
}
