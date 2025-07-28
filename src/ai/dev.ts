import { config } from 'dotenv';
config();

import '@/ai/flows/recommend-books.ts';
import '@/ai/flows/recommend-books-from-prompt.ts';
import '@/ai/flows/find-similar-books.ts';