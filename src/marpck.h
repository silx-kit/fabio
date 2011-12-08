/***********************************************************************
 *
 * marpck.c		
 *
 * Copyright by:        Dr. Claudio Klein
 *                      Marresearch GmbH, Norderstedt
 *
 * Version:     2.0
 * Date:        07/11/2005
 *
 * Based on original version by Jan Pieter Abrahams, University Leiden
 *
 * History
 * Version
 * 2.0		07/11/2005	put_pck renamed into Putmar345Data and
 *				buffered I/O support added
 *                  		get_pck renamed into Getmar345Data
 * 1.1		30/10/1995	As in marcvt version 4.13
 ***********************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <math.h>
#include <ctype.h>
#include <string.h>
#include <unistd.h>

#define BYTE char
#define WORD short int
#define LONG int

#define PACKIDENTIFIER "\nCCP4 packed image, X: %04d, Y: %04d\n"
#define PACKBUFSIZ BUFSIZ
#define DIFFBUFSIZ 16384L
#define max(x, y) (((x) > (y)) ? (x) : (y)) 
#define min(x, y) (((x) < (y)) ? (x) : (y)) 
#define abs(x) (((x) < 0) ? (-(x)) : (x))
#define shift_left(x, n)  (((x) & setbits[32 - (n)]) << (n))
#define shift_right(x, n) (((x) >> (n)) & setbits[32 - (n)])

/*
 * Function prototypes
 */
int          	Getmar345Data	(FILE *, WORD *);
int 		Putmar345Data	(WORD *, int, int, int, FILE *);


static LONG     *diff_words     (WORD *, int, int, LONG *, LONG);
static void     unpack_word     (FILE *, int, int, WORD *);
static void     pack_longs      (LONG *, int, BYTE **, int *, int);
static int      bits            (LONG *, int);
static int      pack_chunk      (LONG *, int, int, int, FILE *);

/***************************************************************************
 * Function: Putmar345Data (ex put_pck)
 * Arguments:
 * 1.)	16-bit image array
 * 2.)	No. of pixels in horizontal direction (x)
 * 3.)	No. of pixels in vertical   direction (y)
 * 4.)	File descriptor for unbuffered I/O (-1 for unused)
 * 5.)	File pointer    for buffered   I/O (NULL for unused)
 ***************************************************************************/
int Putmar345Data(WORD *img, int x, int y, int fd, FILE *fp);

/***************************************************************************
 * Function: bits
 * ==============
 * Returns the number of bits neccesary to encode the longword-array 'chunk'
 * of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
 * 8, 16 or 32.
 ***************************************************************************/
static int bits(LONG *chunk, int n);

/***************************************************************************
 * Function: pack_chunk
 * ====================
 * Packs 'nmbr' LONGs starting at 'lng[0]' into a packed array of 'bitsize'
 * sized elements. If the internal buffer in which the array is packed is full,
 * it is flushed to 'file', making room for more of the packed array. If
 * ('lng == NULL'), the buffer is flushed aswell.
 ***************************************************************************/
static int pack_chunk(LONG *lng, int nmbr, int bitsize, int fdesc, FILE *fp);

/***************************************************************************
 * Function: diff_words
 * ====================
 * Calculates the difference of WORD-sized pixels of an image with the
 * truncated mean value of four of its neighbours. 'x' is the number of fast
 * coordinates of the image 'img', 'y' is the number of slow coordinates,
 * 'diffs' will contain the differences, 'done' defines the index of the pixel
 * where calculating the differences should start. A pointer to the last
 * difference is returned. Maximally DIFFBUFSIZ differences are returned in
 * 'diffs'.
 ***************************************************************************/
LONG *diff_words(WORD *word, int x, int y, LONG *diffs, LONG done);
/***************************************************************************
 * Function: pack_longs
 * ====================
 * Pack 'n' WORDS, starting with 'lng[0]' into the packed array 'target'. The
 * elements of such a packed array do not obey BYTE-boundaries, but are put one

 * behind the other without any spacing. Only the 'bitsiz' number of least
 * significant bits are used. The starting bit of 'target' is 'bit' (bits range
 * from 0 to 7). After completion of 'pack_words()', both '**target' and '*bit'
 * are updated and define the next position in 'target' from which packing
 * could continue.
 ***************************************************************************/
static void pack_longs(LONG *lng, int n, BYTE **target, int *bit, int size);

/***************************************************************************
 * Function: Getmar345Data (ex get_pck)
 ***************************************************************************/
int Getmar345Data(FILE *fp, WORD *img);

/*****************************************************************************
 * Function: unpack_word
 * Unpacks a packed image into the WORD-array 'img'.
 *****************************************************************************/
static void unpack_word(FILE *packfile, int x, int y, WORD *img);
