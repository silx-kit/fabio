

#define SWAP(a,b) {__local int *tmp=a;a=b;b=tmp;}
static void my_group_scan_inclusive_add( 	__local int *inp_buf,
											__local int *out_buf,
											__local int *tmp_buf)
{
    uint lid = get_local_id(0);
    uint ws = get_local_size(0);

    out_buf[lid] = tmp_buf[lid] = inp_buf[lid];
    barrier(CLK_LOCAL_MEM_FENCE);

    for(uint s = 1; s < ws; s <<= 1) {
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

static int my_group_scan_exclusive_add( 	int value,
											__local int *inp_buf,
											__local int *out_buf,
											__local int *tmp_buf)
{
	my_group_scan_inclusive_add(inp_buf, out_buf, tmp_buf);
	uint lid = get_local_id(0);

	out_buf[lid] = (lid >0)? tmp_buf[lid-1] + value : value;
	int ret_val = tmp_buf[get_local_size(0)-1] + value;
	barrier(CLK_LOCAL_MEM_FENCE);
	tmp_buf[lid] = out_buf[lid];
	barrier(CLK_LOCAL_MEM_FENCE);
	return ret_val;
}

/*
Simple CumSum
*/
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
	uint ws = get_local_size(0);
	if (gid<input_size)
	{
		a[lid] = input[gid];
	}
	else
	{
		a[lid] = 0;
	}
	my_group_scan_inclusive_add(a, b, c);
	if (gid<input_size)	output[gid] = b[lid];
}

/*
 * Function called to determine the data type length per char: 1, 3 or 7
 */
static int data_type(uint idx,
		             global int* input,
					 uint input_size)
{
	int current, previous, value, ret_val=0;
	if (idx < input_size)
	{
		current =  input[idx];
		previous = (idx > 0) ? input[idx-1] : 0;
		value = abs(current - previous);
		if (value > 32767)
		{
			ret_val = 7;
		}
		else if (value > 127)
		{
			ret_val = 3;
		}
		else
		{
			ret_val = 1;
		}
	}
	return ret_val;

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
	global int * start_pos,
	global int * stop_pos,
	global int * wg_count,
	local int *local1,
	local int *local2,
	local int *local3)
{
	uint ws = get_local_size(0);
	uint gi = get_group_id(0);
	uint lid = get_local_id(0);
	uint idx, valid_items;
	uint input_offset = start_pos[gi];
	uint output_offset = input_offset;

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
				uint i=0;
				int current, last;
				while (i < ws)
				{
					current = local1[i];
					if (current == -128)
					{
						int next1, next2;
						next1 = ((i+1)<ws) ? local1[i+1] : input[input_offset+i+1];
						next2 = ((i+2)<ws) ? local1[i+2] : input[input_offset+i+2];
						if ((next1 == 0) && (next2 ==-128)) //32 bits exception
						{
							int next3, next4, next5, next6;
							next3 = ((i+3)<ws) ? local1[i+3] : input[input_offset+i+3];
							next4 = ((i+4)<ws) ? local1[i+4] : input[input_offset+i+4];
							next5 = ((i+5)<ws) ? local1[i+5] : input[input_offset+i+5];
							next6 = ((i+6)<ws) ? local1[i+6] : input[input_offset+i+6];
							current = (next6 << 24) | (next5 << 16) | (next4 << 8) | (next3);
							i+=7;
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
			my_group_scan_inclusive_add(local1, local2, local3);
		}
		if (lid<valid_items)
		{
			output[output_offset+lid] = local2[lid];
		}
		input_offset +=  ws;
		output_offset +=  valid_items;
		local2[lid] = 0;
		barrier(CLK_LOCAL_MEM_FENCE);
	}
}



/**
 * \brief byte_offset compression for CBF: first pass: measure the size of the elt. UNUSED
 *
 *
 * @param input: input data in 1D as int32
 * @param output: temporary output as int8 with the size of every single
 * @param input_size: length of the input
 *
 */
kernel void comp_byte_offset0(
		global int* input,
		global int* output,
		uint input_size)
{
	uint gid = get_global_id(0);
	if (gid < input_size)
	{
		output[gid] = data_type(gid, input, input_size);
	}
}

/**
 * \brief byte_offset compression for CBF: First pass: cumsum for position calc,
 * merged with stage0
 *
 *
 * @param input: input data in 1D as int32.
 * @param output: output data in 1D as int32.
 * @param input_size: length of the input
 * @param nbwg: number of workgroup finished
 * @param a,b,c: 3 local buffers of the size of the workgroup
 */

kernel void comp_byte_offset1(
		global int* input,
		global int* output,
		uint input_size,
		uint chunk,
		global int* last_wg,
		global uint* workgroup_counter,
		__local int *a,
		__local int *b,
		__local int *c)
{
	uint lid = get_local_id(0);
	uint ws = get_local_size(0);
	uint wid = get_group_id(0);
	uint nbwg = get_num_groups(0);
	uint to_process = chunk * ws;
	uint start_process = wid *  to_process;
	uint end_process;
	end_process = min(input_size, start_process + to_process);
	int last = 0;
	for (uint offset=start_process; offset< end_process; offset+=ws)
	{
		uint pos = offset + lid;
		if (pos<input_size)
		{
			a[lid] = data_type(pos, input, input_size);
		}
		else
		{
			a[lid] = 0;
		}
		barrier(CLK_LOCAL_MEM_FENCE);
		last = my_group_scan_exclusive_add(last, a, b, c);
		if (pos<input_size)
			output[pos] = b[lid];
	}
	if (lid == 0)
		last_wg[wid] = last;
	barrier(CLK_GLOBAL_MEM_FENCE);

	if (lid == 0)
		a[0] = atomic_inc(workgroup_counter);
	barrier(CLK_GLOBAL_MEM_FENCE);
	barrier(CLK_LOCAL_MEM_FENCE);
	if ((a[0]+1) == nbwg) // we are the last work group
	{
//		Do a cum_sum of all groups results
		a[lid] = last_wg[lid];
		my_group_scan_inclusive_add(a, b, c);
		last_wg[lid] = b[lid];
	}
}


/**
 * \brief byte_offset compression for CBF: Second pass: store the value at the right place
 *
 * Nota: This enforces little-endian storage
 *
 * @param input: input data in 1D as int8
 * @param local_index: input data with output positions, reference
 * @param global_offset: absolute offset of the workgroup, reference
 * @param output: output as int32
 * @param input_size: length of the input
 * @param output_size: length of the output, also size of local_index
 * @param chunk: number of data-point every thread will process
 *
 */
kernel void comp_byte_offset2(
		global int* input,
		global int* local_index,
		global int* global_offset,
		global char* output,
		uint input_size,
		uint output_size,
		uint chunk)
{
	uint gid = get_global_id(0);
	uint wid = get_group_id(0);
	uint ws = get_local_size(0);
	uint lid = get_local_id(0);
	uint to_process = chunk * ws;
	uint start_process = wid *  to_process;
	uint end_process;
	end_process = min(input_size, start_process + to_process);
	int pos_offset = (wid > 0) ? global_offset[wid-1] : 0;
	for (uint offset=start_process; offset< end_process; offset+=ws)
	{
		int current, previous, value, absvalue;
		uint pos = offset + lid;
		if (pos<end_process)
		{
			previous = (pos>0)? input[pos -1]: 0;
			current = input[pos];
			value = current - previous;
			absvalue = abs(value);
			uint dest = pos_offset + local_index[pos];
			if (dest < output_size)
			{
				if (absvalue > 32767)
				{
					output[dest] = -128;
					output[dest+1] = 0;
					output[dest+2] = -128;
					output[dest+3] = (char) (value & 255);
					output[dest+4] = (char) ((value >> 8) & 255);
					output[dest+5] = (char) ((value >> 16) & 255);
					output[dest+6] = (char) (value >> 24);
				}
				else if (absvalue > 127)
				{
					output[dest] = -128;
					output[dest+1] = (char) (value & 255);
					output[dest+2] = (char) (value >> 8);
				}
				else
				{
					output[dest] =  (char) value;
				}
			}
		}
	}
}
