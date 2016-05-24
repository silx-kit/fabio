

#define SWAP(a,b) {__local int *tmp=a;a=b;b=tmp;}
static void work_group_scan_inclusive_add( 	__local int *inp_buf,
											__local int *out_buf,
											__local int *tmp_buf)
{
    uint lid = get_local_id(0);
    uint gs = get_local_size(0);

    out_buf[lid] = tmp_buf[lid] = inp_buf[lid];
    barrier(CLK_LOCAL_MEM_FENCE);

    for(uint s = 1; s < gs; s <<= 1) {
        if(lid > (s-1)) {
        	tmp_buf[lid] = out_buf[lid]+out_buf[lid-s];
        } else {
        	tmp_buf[lid] = out_buf[lid];
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        SWAP(out_buf, tmp_buf);
    }
    tmp_buf[lid] = out_buf[lid];
}

kernel void cumsum(
	global char* input,
	global int* output,
	int input_size,
	int output_size,
	__local int *a,
	__local int *b,
	__local int *c)
{
	uint gid = get_global_id(0);
	uint lid = get_local_id(0);
	uint gs = get_local_size(0);
	if (gid<input_size)
		{
		a[lid] = input[gid];
		}else{
		a[lid] = 0;
		}
	work_group_scan_inclusive_add(a, b, c);
	output[gid] = b[lid];
}

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
	global char * lel,
	global char * lem,
	global int * start_pos
	global int * stop_pos
	global int * wg_count
	local int *local1,
	local int *local2,
	local int *local3)

	)
{
	uint gs = get_local_size(0);
	uint gi = get_group_id(0);
	uint lid = get_local_id(0);
	uint idx, valid_items;
	uint input_offset = start_pos[gi];
	uint output_offset = input_offset;
	char data;
	int value;
	int offset_value=0;


	local2[lid] = 0; // counter for exceptions
	barrier(CLK_LOCAL_MEM_FENCE);
	while (input_offset < input_size)
	{
		idx = lid + input_offset;
		if (idx<input_size)
		{
			local1[lid] = input[idx];
		}
		else
		{
			local1[lid] = 0;
		}
		if (local1[lid] == -128)
		{
			atomic_inc(&local2[0]);
		}
		barrier(CLK_LOCAL_MEM_FENCE);
		if (local2[0])
		{
			valid_items = 0;
			if (lid==0)//serialize scan
			{
				uint i=j=0;
				int current, last;
				while (i<ws)
				{
					current = local1[i];
					if (current == -128)
					{
						int next1, next2;
						next1 = ((i+1)<ws) ? local1[i+1] : input[input_offset+i+1];
						next2 = ((i+2)<ws) ? local1[i+2] : input[input_offset+i+2];
						if ((next1 == 0) && (next2 ==-128)) //32 bits exception
						{
							int next1, next2, next3, next4, next5, next6;
							next3 = ((i+3)<ws) ? local1[i+3] : input[input_offset+i+3];
							next4 = ((i+4)<ws) ? local1[i+4] : input[input_offset+i+4];
							next5 = ((i+5)<ws) ? local1[i+5] : input[input_offset+i+5];
							next6 = ((i+6)<ws) ? local1[i+6] : input[input_offset+i+6];
							current = (next6 << 24) | (next5 << 16) | (next4 << 8) | (next3)
							i+=7
						}
						else
						{
							current = (next2 << 8) | (next1);
							i+=3;

						}
					}
					else
					{
						i+=1;
					}
		            last += current;
		            local2[valid_items] = last;
					valid_items += 1;
				}

			}
		}
		else
		{//perform a normal reduction in the workgroup
			valid_items = ws;
			work_group_scan_inclusive_add(local1, local2, local3);
		}
		if (lid<valid_items)
		{
			data[output_offset+lid] = local2[lid];
		}
		input_offset +=  ws;
		output_offset +=  valid_items;
		local2[lid] = 0;
		barrier(CLK_LOCAL_MEM_FENCE);


	}
}
