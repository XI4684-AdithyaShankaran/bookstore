'use server';

/**
 * @fileOverview Provides book recommendations based on the details of a given book.
 *
 * - findSimilarBooks - A function to retrieve similar book recommendations.
 * - FindSimilarBooksInput - The input type for the findSimilarBooks function.
 * - FindSimilarBooksOutput - The return type for the findSimilarBooks function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const FindSimilarBooksInputSchema = z.object({
  title: z.string().describe('The title of the book.'),
  author: z.string().describe('The author of the book.'),
  description: z.string().describe('The description of the book.'),
});
export type FindSimilarBooksInput = z.infer<typeof FindSimilarBooksInputSchema>;

const FindSimilarBooksOutputSchema = z.object({
  recommendations: z
    .array(z.string())
    .describe('A list of similar book titles and authors.'),
});
export type FindSimilarBooksOutput = z.infer<typeof FindSimilarBooksOutputSchema>;

export async function findSimilarBooks(input: FindSimilarBooksInput): Promise<FindSimilarBooksOutput> {
  return findSimilarBooksFlow(input);
}

const prompt = ai.definePrompt({
  name: 'findSimilarBooksPrompt',
  input: {schema: FindSimilarBooksInputSchema},
  output: {schema: FindSimilarBooksOutputSchema},
  prompt: `You are a book recommendation expert. Based on the details of the book provided, recommend other similar books.

Title: {{{title}}}
Author: {{{author}}}
Description: {{{description}}}

Recommend 5 similar books, listing the title and author for each book.
`,
});

const findSimilarBooksFlow = ai.defineFlow(
  {
    name: 'findSimilarBooksFlow',
    inputSchema: FindSimilarBooksInputSchema,
    outputSchema: FindSimilarBooksOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
