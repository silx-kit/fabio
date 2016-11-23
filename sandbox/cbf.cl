

#define SWAP(a,b) {local int *tmp=a;a=b;b=tmp;}
static void my_group_scan_inclusive_add( 	local int *inp_buf,
											local int *out_buf,
											local int *tmp_buf)
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
    barrier(CLK_LOCAL_MEM_FENCE);
}

static int my_group_scan_exclusive_add( 	int value,
											local int *inp_buf,
											local int *out_buf,
											local int *tmp_buf)
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

static void dummy_sort(local int *data, int left, int right)
{
   for (int i = left ; i < right ; i++)
       for (int j = i + 1; j <= right; j++)
       {
           if (data[i] > data[j])
           {
               int aux = data[i];
               data[i] = data[j];
               data[j] = aux;
           }
       }
}

/*
Simple CumSum
*/
kernel void cumsum(
	global char* input,
	global int* output,
	int input_size,
	int output_size,
	local int *a,
	local int *b,
	local int *c)
{
	uint gid = get_global_id(0);
	uint lid = get_local_id(0);
	//uint ws = get_local_size(0);
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
 * Stage 0 initialize the size_array to -1
 * Stage 1 write 0 or 1 to size_array depending on in the pixel size
 * stage 2 perform a cum_sum on the index to know where to read
 * stage 3 perform a cum_sum on the values
 */
kernel void dec_byte_offset0(
	global int* indices,
	int input_size)
{
	uint gid = get_group_id(0);
	if (gid<input_size)
	{
		indices[gid] = -1;
	}
}

kernel void dec_byte_offset1(
		global char* input,
		global int* indices,
		uint input_size,
		uint chunk,
		global int* start_position,
		global int* end_position,
		local int *local_a,
		local int *local_b
		)
{
	uint lid = get_local_id(0);
	uint ws = get_local_size(0);
	uint wid = get_group_id(0);
	uint nbwg = get_num_groups(0);

	local int exceptions[1];
	local int local_start[1];
	local int new_offset[1];
	local int value_offset[1];

	uint to_process = chunk * ws;
	uint start_process = wid *  to_process;
	uint actual_start = 0;
	uint actual_end;
	uint end_process = min(input_size, start_process + to_process);
	int last = 0;
	char first = (wid==0)? 0: 1;
	if (lid == 0)
	{
		exceptions[0] = 0;
		value_offset[0] = 0;
	}
	local_b[lid] = ws;
	barrier(CLK_LOCAL_MEM_FENCE);


	for (uint offset=start_process; offset< end_process; offset+=ws)
	{
		uint pos = offset + lid;
		if (pos<input_size)
		{
			local_a[lid] = input[pos];
		}
		else
		{
			local_a[lid] = 0;
		}
		if (local_a[lid] == -128)
		{
			int exc_pos;
			exc_pos = atomic_inc(exceptions);
			local_b[exc_pos] = lid;
		}
		barrier(CLK_LOCAL_MEM_FENCE);
		if (first)
		{
			if (exceptions[0])
			{
                if (lid==0)
                {
                	int last_ext = 0;
                	dummy_sort(local_b, 0, exceptions[0]);
                	for (int i=0; i<exceptions[0]; i++)
                	{
                		if ((local_b[i]-last_ext)<=4)
                		{
                			last_ext = local_b[i];
                		}
                		else
                		{
                			local_start[0] = last_ext + 5;
                			break;
                		}
                	}
                }
			}
			else
			{
				local_start[0] = 5;
			}
			barrier(CLK_LOCAL_MEM_FENCE);
			actual_start = local_start[0];
			start_position[wid] = start_process + local_start[0];
		}
		else
		{
			actual_start = 0;
		}
		if ((actual_start==0) && (exceptions[0] == 0))
		{
			local_b[lid] = lid + value_offset[0];

			if (lid==0)
				value_offset[0] = local_b[ws-1]
		}
		else
		{
			if (lid==0)
			{
				for (int i=actual_start, i<ws, i++)
				{

				}
			}
		}

		barrier(CLK_LOCAL_MEM_FENCE);
		offset += new_offset[0];
		value_offset=local_b[lid]

	}
}
/**
 * \brief byte_offset decompression for CBF: Second pass: store the value at the right place
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
kernel void dec_byte_offset2(
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
		local int *a,
		local int *b,
		local int *c,
		//volatile local int *d,
		global int* ddebug1,
		global int* ddebug2,
		global int* ddebug3)
{
	uint lid = get_local_id(0);
	uint ws = get_local_size(0);
	uint wid = get_group_id(0);
	uint nbwg = get_num_groups(0);
	local int d[1];
	uint to_process = chunk * ws;
	uint start_process = wid *  to_process;
	uint end_process = min(input_size, start_process + to_process);
	ddebug2[wid] = end_process;
	ddebug3[wid] = start_process;
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
	{
		last_wg[wid] = last;
		ddebug1[wid] = d[0] = atomic_inc(workgroup_counter);
	}
	barrier(CLK_LOCAL_MEM_FENCE);
	if ((d[0]+1) == nbwg) // we are the last work group
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
