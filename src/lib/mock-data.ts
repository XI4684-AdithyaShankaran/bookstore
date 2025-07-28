import type { Book } from './types';

export const mockBooks: Book[] = [
  {
    id: 1,
    title: 'To Kill a Mockingbird',
    author: 'Harper Lee',
    description:
      'The unforgettable novel of a childhood in a sleepy Southern town and the crisis of conscience that rocked it, To Kill A Mockingbird became both an instant bestseller and a critical success when it was first published in 1960. It went on to win the Pulitzer Prize in 1961 and was later made into an Academy Award-winning film, also a classic.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Classic',
    rating: 4.8,
  },
  {
    id: 2,
    title: '1984',
    author: 'George Orwell',
    description:
      'Among the seminal texts of the 20th century, Nineteen Eighty-Four is a rare work that grows more haunting as its futuristic purgatory becomes more real. Published in 1949, the book offers political satirist George Orwell\'s nightmare vision of a totalitarian, bureaucratic world and one poor stiff\'s attempt to find individuality.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Dystopian',
    rating: 4.7,
  },
  {
    id: 3,
    title: 'The Great Gatsby',
    author: 'F. Scott Fitzgerald',
    description:
      'The Great Gatsby, F. Scott Fitzgerald\'s third book, stands as the supreme achievement of his career. This exemplary novel of the Jazz Age has been acclaimed by generations of readers. The story of the fabulously wealthy Jay Gatsby and his new love for the beautiful Daisy Buchanan, of lavish parties on Long Island is an exquisitely crafted tale of America in the 1920s.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Classic',
    rating: 4.5,
  },
  {
    id: 4,
    title: 'The Catcher in the Rye',
    author: 'J.D. Salinger',
    description:
      'The hero-narrator of The Catcher in the Rye is an ancient child of sixteen, a native New Yorker named Holden Caufield. Through circumstances that tend to preclude adult, secondhand description, he leaves his prep school in Pennsylvania and goes underground in New York City for three days.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Classic',
    rating: 4.2,
  },
  {
    id: 5,
    title: 'Dune',
    author: 'Frank Herbert',
    description:
      'Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, heir to a noble family tasked with ruling an inhospitable world where the only thing of value is the "spice" melange, a drug capable of extending life and enhancing consciousness. When House Atreides is betrayed, the destruction of Paul\'s family will set the boy on a journey toward a destiny greater than he could ever have imagined.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Sci-Fi',
    rating: 4.9,
  },
  {
    id: 6,
    title: 'Pride and Prejudice',
    author: 'Jane Austen',
    description:
      'Since its immediate success in 1813, Pride and Prejudice has remained one of the most popular novels in the English language. Jane Austen called this brilliant work "her own darling child" and its vivacious heroine, Elizabeth Bennet, "as delightful a creature as ever appeared in print."',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Romance',
    rating: 4.8,
  },
  {
    id: 7,
    title: 'The Hobbit',
    author: 'J.R.R. Tolkien',
    description:
      'In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to eat: it was a hobbit-hole, and that means comfort.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Fantasy',
    rating: 4.9,
  },
  {
    id: 8,
    title: 'Brave New World',
    author: 'Aldous Huxley',
    description:
      'Aldous Huxley\'s profoundly important classic of world literature, Brave New World is a searching vision of an unequal, technologically-advanced future where humans are genetically bred, socially indoctrinated, and pharmaceutically anesthetized to passively uphold an authoritarian ruling order.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Dystopian',
    rating: 4.6,
  },
  {
    id: 9,
    title: 'Moby Dick',
    author: 'Herman Melville',
    description: 'The narrative of the obsessive quest of Ahab, captain of the whaling ship Pequod, for revenge on Moby Dick, the giant white sperm whale that on the previous whaling voyage bit off Ahab\'s leg at the knee.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Adventure',
    rating: 4.1
  },
  {
    id: 10,
    title: 'War and Peace',
    author: 'Leo Tolstoy',
    description: 'A literary work mixed with chapters on history and philosophy by the Russian author Leo Tolstoy. It was first published serially, then published in its entirety in 1869. It is regarded as one of Tolstoy\'s finest literary achievements and remains an internationally praised classic of world literature.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Historical Fiction',
    rating: 4.4
  },
  {
    id: 11,
    title: 'The Lord of the Rings',
    author: 'J.R.R. Tolkien',
    description: 'A young hobbit, Frodo, who has found the One Ring that belongs to the Dark Lord Sauron, begins his journey with eight companions to Mount Doom, the only place where it can be destroyed.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Fantasy',
    rating: 5.0
  },
  {
    id: 12,
    title: 'Foundation',
    author: 'Isaac Asimov',
    description: 'For twelve thousand years the Galactic Empire has ruled supreme. Now it is dying. But only Hari Seldon, creator of the revolutionary science of psychohistory, can see into the future—to a dark age of ignorance, barbarism, and warfare that will last thirty thousand years. To preserve knowledge and save mankind, Seldon gathers the best minds in the Empire—both scientists and scholars—and brings them to a bleak planet at the edge of the galaxy to serve as a beacon of hope for future generations.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Sci-Fi',
    rating: 4.8
  },
  {
    id: 13,
    title: 'The Hitchhiker\'s Guide to the Galaxy',
    author: 'Douglas Adams',
    description: 'Seconds before the Earth is demolished to make way for a galactic freeway, Arthur Dent is plucked off the planet by his friend Ford Prefect, a researcher for the revised edition of The Hitchhiker\'s Guide to the Galaxy who, for the last fifteen years, has been posing as an out-of-work actor.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Sci-Fi',
    rating: 4.7
  },
  {
    id: 14,
    title: 'The Chronicles of Narnia',
    author: 'C.S. Lewis',
    description: 'Journeys to the end of the world, fantastic creatures, and epic battles between good and evil—what more could any reader ask for in one book? The book that has it all is The Lion, the Witch and the Wardrobe, written in 1949 by C. S. Lewis. But Lewis did not stop there. Six more books followed, and together they became known as The Chronicles of Narnia.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Fantasy',
    rating: 4.8
  },
  {
    id: 15,
    title: 'The Picture of Dorian Gray',
    author: 'Oscar Wilde',
    description: 'Oscar Wilde’s only novel is the dreamlike story of a young man who sells his soul for eternal youth and beauty. In this Faustian tale, Dorian Gray is a breathtakingly handsome young man whose portrait captures his exquisite beauty. But he is seduced into a life of sin and degradation, and as he remains young and beautiful, his portrait becomes a hideous record of his depravity.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Gothic',
    rating: 4.5
  },
  {
    id: 16,
    title: 'Frankenstein',
    author: 'Mary Shelley',
    description: 'A monster assembled by a scientist from parts of dead bodies, an animated corpse—these are the images that have fired the imaginations of generations of readers. But the story of Victor Frankenstein and his monstrous creation is more than a simple horror story. It is a tale of obsession, of the limits of human creativity, and of the destructive power of guilt.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Gothic',
    rating: 4.4
  },
  {
    id: 17,
    title: 'The Alchemist',
    author: 'Paulo Coelho',
    description: 'Paulo Coelho\'s enchanting novel has inspired a devoted following around the world. This story, dazzling in its powerful simplicity and soul-stirring wisdom, is about an Andalusian shepherd boy named Santiago who travels from his homeland in Spain to the Egyptian desert in search of a treasure buried in the Pyramids. Along the way he meets a Gypsy woman, a man who calls himself king, and an alchemist, all of whom point Santiago in the direction of his quest.',
    coverImage: 'https://placehold.co/400x600/478CCA/F0F4F7',
    genre: 'Fantasy',
    rating: 4.6
  },
  {
    id: 18,
    title: 'One Hundred Years of Solitude',
    author: 'Gabriel Garcia Marquez',
    description: 'One of the twentieth century\'s most beloved and acclaimed novels, One Hundred Years of Solitude tells the story of the rise and fall, birth and death of the mythical town of Macondo through the history of the Buendía family. Inventive, amusing, magnetic, sad, and alive with unforgettable men and women—brimming with truth, compassion, and a lyrical magic that strikes the soul—this novel is a masterpiece in the art of fiction.',
    coverImage: 'https://placehold.co/400x600/F2A63F/000000',
    genre: 'Magical Realism',
    rating: 4.3
  }
];
