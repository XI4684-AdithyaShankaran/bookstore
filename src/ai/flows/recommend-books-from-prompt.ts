// src/ai/flows/recommend-books-from-prompt.ts
'use server';
/**
 * @fileOverview Recommends books based on a text prompt.
 *
 * - recommendBooksFromPrompt - A function that takes a text prompt and returns book recommendations.
 * - RecommendBooksFromPromptInput - The input type for the recommendBooksFromPrompt function.
 * - RecommendBooksFromPromptOutput - The return type for the recommendBooksFromPrompt function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const RecommendBooksFromPromptInputSchema = z.object({
  prompt: z.string().describe('A text prompt describing the type of books to recommend.'),
});
export type RecommendBooksFromPromptInput = z.infer<typeof RecommendBooksFromPromptInputSchema>;

const RecommendBooksFromPromptOutputSchema = z.object({
  bookRecommendations: z.array(
    z.object({
      title: z.string().describe('The title of the book.'),
      author: z.string().describe('The author of the book.'),
      description: z.string().describe('A short description of the book.'),
    })
  ).describe('A list of book recommendations based on the prompt.'),
});
export type RecommendBooksFromPromptOutput = z.infer<typeof RecommendBooksFromPromptOutputSchema>;

export async function recommendBooksFromPrompt(input: RecommendBooksFromPromptInput): Promise<RecommendBooksFromPromptOutput> {
  return recommendBooksFromPromptFlow(input);
}

const prompt = ai.definePrompt({
  name: 'recommendBooksFromPromptPrompt',
  input: {schema: RecommendBooksFromPromptInputSchema},
  output: {schema: RecommendBooksFromPromptOutputSchema},
  prompt: `You are a book recommendation expert. Based on the user's prompt, you will provide a list of book recommendations.

  Prompt: {{{prompt}}}

  Please provide the book recommendations in the following format:
  {
    bookRecommendations: [
      {
        title: "Book Title",
        author: "Author Name",
        description: "A short description of the book."
      }
    ]
  }`,
});

const recommendBooksFromPromptFlow = ai.defineFlow(
  {
    name: 'recommendBooksFromPromptFlow',
    inputSchema: RecommendBooksFromPromptInputSchema,
    outputSchema: RecommendBooksFromPromptOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
