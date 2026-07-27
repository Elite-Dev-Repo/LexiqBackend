import random
from django.core.management.base import BaseCommand
from QuestionsDirectory.models import QuestionDeck, Question, QuestionOption

from QuestionsDirectory.word_lists import WORDS_DECK_1, WORDS_DECK_2, WORDS_DECK_3


class Command(BaseCommand):
    help = "Generate 3000 advanced vocabulary questions (1000 per deck)"

    def handle(self, *args, **options):
        all_decks = {1: WORDS_DECK_1, 2: WORDS_DECK_2, 3: WORDS_DECK_3}
        difficulties = ["easy", "medium", "hard"]

        for deck_id, word_list in all_decks.items():
            try:
                deck = QuestionDeck.objects.get(id=deck_id)
            except QuestionDeck.DoesNotExist:
                self.stderr.write(f"Deck id={deck_id} not found. Skipping.")
                continue

            existing = {
                q.word.lower()
                for q in Question.objects.filter(deck=deck).only("word")
            }

            created = 0
            skipped = 0
            for i, (word, definition, example, distractors) in enumerate(word_list):
                if word.lower() in existing:
                    skipped += 1
                    continue

                q = Question.objects.create(
                    deck=deck,
                    word=word,
                    definition=definition,
                    usage_example=example,
                    difficulty=difficulties[i % 3],
                )

                options = distractors + [word]
                random.shuffle(options)
                QuestionOption.objects.bulk_create([
                    QuestionOption(question=q, option_text=t, is_correct=(t == word))
                    for t in options
                ])
                created += 1
                existing.add(word.lower())

            self.stdout.write(self.style.SUCCESS(
                f"Deck '{deck.name}': {created} created, {skipped} skipped"
            ))

        self.stdout.write(self.style.SUCCESS("Done!"))
