# # path = r"C:\Coding\stockfish_15_win_x64_avx2\stockfish_15_x64_avx2.exe"
import asyncio
import chess
import chess.engine

async def main() -> None:
    transport, engine = await chess.engine.popen_uci(r"C:\Coding\stockfish_15_win_x64_avx2\stockfish_15_x64_avx2.exe")

    board = chess.Board()
    while not board.is_game_over():
        print(board, end='\n\n')
        result = await engine.play(board, chess.engine.Limit(time=0.1))
        board.push(result.move)

    await engine.quit()

asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(main())