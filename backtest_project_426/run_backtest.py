# run_backtest.py
import sys
from backtest_main import main

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n回测被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"回测出错: {e}")
        sys.exit(1)