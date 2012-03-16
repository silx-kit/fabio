/* Some general defines: */


#define PACKIDENTIFIER "\nCCP4 packed image, X: %04d, Y: %04d\n"
/* This string defines the start of a packed image. An image file is scanned
   until this string is encountered, the size of the unpacked image is
   determined from the values of X and Y (which are written out as formatted
   ascii numbers), and the packed image is expected to start immediately after
   the null-character ending the string. */

#define V2IDENTIFIER "\nCCP4 packed image V2, X: %04d, Y: %04d\n"
/* This string defines the start of a packed image. An image file is scanned
   until this string is encountered, the size of the unpacked image is
   determined from the values of X and Y (which are written out as formatted
   ascii numbers), and the packed image is expected to start immediately after
   the null-character ending the string. */

#define PACKBUFSIZ BUFSIZ
/* Size of internal buffer in which the packed array is stored during transit
   form an unpacked image to a packed image on disk. It is set to the size
   used by the buffered io-routines given in <stdio.h>, but it could be
   anything. */

#define DIFFBUFSIZ 16384L
/* Size of the internal buffer in which the differences between neighbouring
   pixels are stored prior to compression. The image is therefore compressed
   in DIFFBUFSIZ chunks. Decompression does not need to know what DIFFBUFSIZ
   was when the image was compressed. By increasing this value, the image
   can be compressed into a packed image which is a few bytes smaller. Do
   not decrease the value of DIFFBUFSIZ below 128L. */

#define BYTE char
/* BYTE is a one byte integer. */

#define WORD short int
/* WORD is a two-byte integer. */

#define LONG int
/* LONG is a four byte integer. */
/* Dave Love 5/7/94: using `int' gets you 4 bytes on the 32-bit Unix
   (and VAX) systems I know of and also on (64-bit) OSF/1 Alphas which
   have 64-bit longs.  (This definition previously used `long'.) */



/******************************************************************************/

/* Some usefull macros used in the code of this sourcefile: */


#define max(x, y) (((x) > (y)) ? (x) : (y))
/* Returns maximum of x and y. */

#define min(x, y) (((x) < (y)) ? (x) : (y))
/* Returns minimum of x and y. */

#undef abs			/* avoid complaint from DEC C, at least */
#define abs(x) (((x) < 0) ? (-(x)) : (x))
/* Returns the absolute value of x. */

/* Used to be 'static const LONG' but const declaration gives trouble on HPs */
#ifndef SKIP_SETBITS
static LONG setbits[33] =
                         {0x00000000L, 0x00000001L, 0x00000003L, 0x00000007L,
			  0x0000000FL, 0x0000001FL, 0x0000003FL, 0x0000007FL,
			  0x000000FFL, 0x000001FFL, 0x000003FFL, 0x000007FFL,
			  0x00000FFFL, 0x00001FFFL, 0x00003FFFL, 0x00007FFFL,
			  0x0000FFFFL, 0x0001FFFFL, 0x0003FFFFL, 0x0007FFFFL,
			  0x000FFFFFL, 0x001FFFFFL, 0x003FFFFFL, 0x007FFFFFL,
			  0x00FFFFFFL, 0x01FFFFFFL, 0x03FFFFFFL, 0x07FFFFFFL,
			  0x0FFFFFFFL, 0x1FFFFFFFL, 0x3FFFFFFFL, 0x7FFFFFFFL,
                          0xFFFFFFFFL};
/* This is not a macro really, but I've included it here anyway. Upon indexing,
   it returns a LONG with the lower (index) number of bits set. It is equivalent
   to the following macro:
     #define setbits(n) (((n) == 32) : ((1L << (n)) - 1) : (-1L))
   Indexing the const array should usually be slightly faster. */
#endif

#define shift_left(x, n)  (((x) & setbits[32 - (n)]) << (n))
/* This macro is included because the C standard does not properly define a
   left shift: on some machines the bits which are pushed out at the left are
   popped back in at the right. By masking, the macro prevents this behaviour.
   If you are sure that your machine does not pops bits back in, you can speed
   up the code insignificantly by taking out the masking. */

#define shift_right(x, n) (((x) >> (n)) & setbits[32 - (n)])
/* See comment on left shift. */



/******************************************************************************/




/* Functions required for packing: */

#if defined (PROTOTYPE)


void pack_wordimage_c(WORD *img, int x, int y, char *filename);
/* Pack image 'img', containing 'x * y' WORD-sized pixels into 'filename'.
   This function generates Version 1 images! */
void pack_wordimage_copen(WORD *img, int x, int y, FILE *packfile)

void pack_longimage_c(LONG *img, int x, int y, char *filename);
/* Pack image 'img', containing 'x * y' LONG-sized pixels into 'filename'.
   This function generates Version 1 images! */
void pack_longimage_copen(LONG *img, int x, int y, FILE *packfile)


void v2pack_wordimage_c(WORD *img, int x, int y, char *filename);
/* Pack image 'img', containing 'x * y' WORD-sized pixels into 'filename'.
   This function generates Version 2 images! */

void v2pack_longimage_c(LONG *img, int x, int y, char *filename);
/* Pack image 'img', containing 'x * y' LONG-sized pixels into 'filename'.
   This function generates Version 2 images! */


/* Functions required for unpacking: */
void unpack_word(FILE *packfile, int x, int y, WORD *img);

void readpack_word_c(WORD *img, char *filename);
/* Unpacks packed image from 'filename' into the WORD-array 'img'. Scans the
   file defined by 'filename' until the PACKIDENTIFIER is found, then unpacks
   starting from there. */

void readpack_long_c(LONG *img, char *filename);
/* Unpacks packed image from 'filename' into the LONG-array 'img'. Scans the
   file defined by 'filename' until the PACKIDENTIFIER is found, then unpacks
   starting from there. */

void imsiz_c(char *filename, LONG *x, LONG *y);
/* Determines the size of the the packed image "filename" after unpacking. The
   dimensions are returned in x and y. */

#endif  /* (PROTOTYPE) */

