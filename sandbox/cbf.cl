/**
 * \brief byte_offset decompression for CBF
 *
 *
 * @param input: input data in 1D as int8
 * @param output: oupyt as int32
 * @param input_size: length of the input
 * @param output_size: length of the output
 * @param lel: length of every element
 *
 */



kernel void dec_byte_offset(
	global char* input,
	global int* output,
	int input_size,
	int output_size,
	global char * lel
	)
{
	int input_offset = 0;
	int output_offset = 0;
	int lidx = get_local_id(0);
	int idx = lidx;
	char data;
	int value;

	while (input_offset < input_size)
	{

		idx = lidx + input_offset;
		//		Step one: flag 0x80
		if (idx<input_size)
		{
			data = input[idx];
			if (data == -128)
			{
				if ((idx>1) && (input[idx-1]==0) && (input[idx-2]==-128))
				{
					lel[idx] = 0;
				}else if ((idx<input_size-2) && (input[idx+1]==0) && (input[idx+2]==-128))
				{
					lel[idx] = 7;
				}else{
					lel[idx] = 3;
				}
			}else{
				lel[idx] = 1;
			}
//			Sync

		}
		input_offset +=  get_local_size(0);


	}
}
