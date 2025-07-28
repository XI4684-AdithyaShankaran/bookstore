'use server';

/**
 * @fileOverview Book recommendation flow based on user bookshelves.
 *
 * - recommendBooks - A function that recommends books based on the books in the user's bookshelves.
 * - RecommendBooksInput - The input type for the recommendBooks function.
 * - RecommendBooksOutput - The return type for the recommendBooks function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const RecommendBooksInputSchema = z.object({
  bookshelfContents: z
    .string()
    .describe('A list of book titles and authors in the user\'s bookshelves.'),
  numberOfRecommendations: z
    .number()
    .default(3)
    .describe('The number of book recommendations to generate.'),
});
export type RecommendBooksInput = z.infer<typeof RecommendBooksInputSchema>;

const RecommendBooksOutputSchema = z.object({
  recommendations: z
    .array(z.string())
    .describe('A list of book recommendations based on the bookshelf contents.'),
});
export type RecommendBooksOutput = z.infer<typeof RecommendBooksOutputSchema>;

export async function recommendBooks(input: RecommendBooksInput): Promise<RecommendBooksOutput> {
  return recommendBooksFlow(input);
}

const prompt = ai.definePrompt({
  name: 'recommendBooksPrompt',
  input: {schema: RecommendBooksInputSchema},
  output: {schema: RecommendBooksOutputSchema},
  prompt: `You are a book recommendation expert. Given the books in the user's bookshelves, recommend {{numberOfRecommendations}} additional books they might enjoy.

Bookshelf Contents: {{{bookshelfContents}}}

Recommendations:`,
});

const recommendBooksFlow = ai.defineFlow(
  {
    name: 'recommendBooksFlow',
    inputSchema: RecommendBooksInputSchema,
    outputSchema: RecommendBooksOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
