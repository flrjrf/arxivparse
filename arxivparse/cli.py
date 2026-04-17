"""CLI entry point for arxivparse."""

import logging
import sys
from pathlib import Path

from jsonargparse import ArgumentParser

from arxivparse.errors import Arxiv2TextError
from arxivparse.pipeline import convert_arxiv_to_text


def _setup_logging(verbose: int, quiet: bool) -> None:
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(args: list[str] | None = None) -> None:
    parser = ArgumentParser(
        prog="arxivparse",
        description="Convert arXiv papers to plain text using LaTeXML.",
    )
    parser.add_argument("arxiv_ids", nargs="+", help="arXiv ID(s) to convert")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output file (single paper)")
    parser.add_argument("-d", "--output_dir", type=Path, default=Path("."), help="Output directory")
    parser.add_argument("-k", "--keep_temp", action="store_true", help="Keep temp files")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-q", "--quiet", action="store_true")

    opts = parser.parse_args(args)
    _setup_logging(opts.verbose, opts.quiet)
    logger = logging.getLogger(__name__)

    if len(opts.arxiv_ids) == 1 and opts.output:
        try:
            result = convert_arxiv_to_text(
                opts.arxiv_ids[0],
                output_path=opts.output,
                keep_temp=opts.keep_temp,
            )
            print(result)
        except Arxiv2TextError as e:
            logger.error("Failed to convert %s: %s", opts.arxiv_ids[0], e)
            sys.exit(1)
    else:
        failures = 0
        for arxiv_id in opts.arxiv_ids:
            try:
                out = opts.output_dir / f"{arxiv_id.replace('/', '_')}.txt"
                result = convert_arxiv_to_text(
                    arxiv_id,
                    output_path=out,
                    keep_temp=opts.keep_temp,
                )
                print(result)
            except Arxiv2TextError as e:
                logger.error("FAILED %s: %s", arxiv_id, e)
                failures += 1
        if failures:
            sys.exit(1)


if __name__ == "__main__":
    main()
