import unittest

from app.services.document_chunking import chunk_text


class DocumentChunkingTests(unittest.TestCase):
    def test_empty_input_returns_empty_list(self):
        self.assertEqual(
            chunk_text(""),
            [],
        )

    def test_shorter_input_returns_single_chunk(self):
        text = "short text"

        self.assertEqual(
            chunk_text(
                text,
                chunk_size=20,
                chunk_overlap=5,
            ),
            [text],
        )

    def test_exact_chunk_size_returns_single_chunk(self):
        text = "abcdefghij"

        self.assertEqual(
            chunk_text(
                text,
                chunk_size=10,
                chunk_overlap=2,
            ),
            [text],
        )

    def test_longer_input_is_split_into_chunks(self):
        text = "abcdefghijklmno"

        chunks = chunk_text(
            text,
            chunk_size=5,
            chunk_overlap=0,
        )

        self.assertEqual(
            chunks,
            ["abcde", "fghij", "klmno"],
        )

    def test_multiple_chunks_share_expected_overlap(self):
        text = "abcdefghijkl"

        chunks = chunk_text(
            text,
            chunk_size=5,
            chunk_overlap=2,
        )

        self.assertEqual(
            chunks,
            ["abcde", "defgh", "ghijk", "jkl"],
        )

        for previous, current in zip(
            chunks,
            chunks[1:],
        ):
            self.assertEqual(
                previous[-2:],
                current[:2],
            )

    def test_final_chunk_can_be_shorter_than_chunk_size(self):
        chunks = chunk_text(
            "abcdefghijk",
            chunk_size=5,
            chunk_overlap=1,
        )

        self.assertEqual(
            chunks[-1],
            "ijk",
        )
        self.assertLess(
            len(chunks[-1]),
            5,
        )

    def test_chunks_preserve_source_order_and_cover_text(self):
        text = "abcdefghijklmnopqrstuvwxyz"

        chunks = chunk_text(
            text,
            chunk_size=7,
            chunk_overlap=2,
        )

        reconstructed = chunks[0]

        for chunk in chunks[1:]:
            reconstructed += chunk[2:]

        self.assertEqual(
            reconstructed,
            text,
        )

        self.assertTrue(
            all(
                len(chunk) <= 7
                for chunk in chunks
            )
        )

    def test_rejects_non_positive_chunk_size(self):
        for chunk_size in (0, -1):
            with self.subTest(
                chunk_size=chunk_size,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "chunk_size must be greater than 0",
                ):
                    chunk_text(
                        "text",
                        chunk_size=chunk_size,
                    )

    def test_rejects_negative_chunk_overlap(self):
        with self.assertRaisesRegex(
            ValueError,
            "chunk_overlap must be greater than or equal to 0",
        ):
            chunk_text(
                "text",
                chunk_size=10,
                chunk_overlap=-1,
            )

    def test_rejects_overlap_equal_to_or_larger_than_chunk_size(self):
        for chunk_overlap in (5, 6):
            with self.subTest(
                chunk_overlap=chunk_overlap,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "chunk_overlap must be smaller than chunk_size",
                ):
                    chunk_text(
                        "text",
                        chunk_size=5,
                        chunk_overlap=chunk_overlap,
                    )

    def test_output_is_deterministic(self):
        text = "abcdefghijklmnopqrstuvwxyz"

        first = chunk_text(
            text,
            chunk_size=8,
            chunk_overlap=3,
        )
        second = chunk_text(
            text,
            chunk_size=8,
            chunk_overlap=3,
        )

        self.assertEqual(
            first,
            second,
        )


if __name__ == "__main__":
    unittest.main()
