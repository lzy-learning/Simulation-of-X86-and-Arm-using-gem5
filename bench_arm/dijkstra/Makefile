all:  dijkstra_large dijkstra_small

CC=arm-linux-gnueabi-gcc-5

dijkstra_large: dijkstra_large.c Makefile
	${CC} -static dijkstra_large.c -O3 -o dijkstra_large

dijkstra_small: dijkstra_small.c Makefile
	${CC} -static dijkstra_small.c -O3 -o dijkstra_small 

clean:
	rm -rf dijkstra_large dijkstra_small output*
