import time
import scraper
import parser


def main():
    scraper.main()
    parser.main(is_local=True)


if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"✅ Run Time is {time.time() - start_time:.2f} seconds")
