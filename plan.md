# **Project: The Evolution of a Metrics Storage Engine**

This project demonstrates the progressive optimization of time-series metric data storage, moving from a simple, human-readable format to a highly compressed, efficient binary format. Each step is a self-contained Python script that takes a generated dataset and writes it to disk, reporting the final storage size.

## **Achievement Summary**

✅ **COMPLETED**: All phases successfully implemented with advanced optimizations  
🎯 **Final Result**: 54.58x compression vs NDJSON baseline  
🏆 **Enhanced Compression**: 24.2% improvement over original compression tricks  
📊 **Storage Efficiency**: 3.19 bytes per data point with enhanced algorithms  
🔧 **Dataset Options**: Small/Big/Huge (up to 100M points) with comprehensive documentation

## **The Data Model**

All steps will operate on a consistent, generated dataset representing typical observability metrics. A single data point will consist of:

* **Timestamp:** A 64-bit integer (e.g., nanoseconds since epoch).  
* **Metric Name:** A string (e.g., http\_requests\_total).  
* **Value:** A 64-bit float.  
* **Labels/Tags:** A dictionary of key-value strings (e.g., {"host": "server-a", "region": "us-east-1", "status\_code": "200"}).

## **Phase 0: Data Generation**

**Goal:** Create a realistic, yet compressible, dataset.

**Implementation (00\_generate\_data.py):**

1. Define a set of metric names and possible label values.  
2. Generate several distinct time series (unique combinations of metric name \+ labels).  
3. For each series, generate timestamps at a semi-regular interval (e.g., 15 seconds \+ a small random jitter).  
4. Generate values that show some correlation (e.g., a sine wave, a random walk) to mimic real-world data.  
5. Output this data as a simple list of Python dictionaries to be consumed by the following scripts.

## **Phase 1: The Baseline \- Denormalized NDJSON**

**Goal:** Establish a simple, human-readable, and highly inefficient baseline.

**Implementation (01\_ndjson\_storage.py):**

1. Read the generated data.  
2. For each data point, serialize the full dictionary (timestamp, name, value, labels) to a JSON string.  
3. Write each JSON string as a new line in a file (metrics.ndjson).  
4. Calculate and print the final file size.

**Rationale:**

* **Pro:** Extremely easy to debug with tools like grep, jq, and awk.  
* **Con (The "Problem"):** Massively redundant. Keys ("timestamp", "value", etc.) and label values ("host": "server-a") are repeated for every single data point. Numbers are stored inefficiently as text.

## **Phase 2: Going Columnar \- Grouping by Series**

**Goal:** Restructure the data from rows to columns, grouping by time series. This is the single most important conceptual shift.

**Implementation (02\_columnar\_storage.py):**

1. Read the generated data.  
2. Create a "series dictionary" or "symbol table". Iterate through the data and assign a unique integer ID to each unique time series (metric name \+ labels).  
3. Restructure the data into a dictionary where keys are the series IDs. The values will be objects containing two lists: one for timestamps and one for values.  
   {  
     "series\_metadata": {  
       "0": {"name": "cpu\_usage", "host": "server-a"},  
       "1": {"name": "cpu\_usage", "host": "server-b"}  
     },  
     "series\_data": {  
       "0": {  
         "timestamps": \[167..., 167..., ...\],  
         "values":     \[0.75, 0.76, ...\]  
       },  
       "1": { ... }  
     }  
   }

4. Serialize this entire structure to a single file using a binary format like MessagePack or pickle (metrics.columnar.msgpack).  
5. Calculate and print the file size.

**Rationale:**

* **Pro:** Eliminates the repetition of metadata for each point. Sets the stage for powerful column-specific compression. Queries for a single series are now much faster (read one block instead of scanning a huge file).  
* **Counterpoint:** The file is no longer easily streamable or appendable. Writing a single new data point requires rewriting the entire structure. This introduces the concept of "blocks" or "chunks" that real TSDBs use to manage this. For this project, we can ignore that complexity and write a single file.

## **Phase 3: Compressing the Columns \- Specialized Encodings**

**Goal:** Apply specialized, aggressive compression techniques to each column, leveraging the data's structure.

**Implementation (03\_compressed\_columnar.py):**

1. Start with the columnar structure from Phase 2\.  
2. **Timestamp Compression (Double-Delta Encoding):**  
   * For each timestamp array, calculate the delta (t\[i\] \- t\[i-1\]).  
   * Calculate the delta-of-deltas (delta\[i\] \- delta\[i-1\]). This will result in many small numbers, and many zeros if the scrape interval is constant.  
   * Store the initial timestamp, the first delta, and then the list of double-deltas.  
3. **Value Compression (Gorilla/XOR Encoding):**  
   * For each float value array, store the first value as-is.  
   * For subsequent values, calculate the XOR of the current value's 64-bit representation with the previous one. If values are close, the result will have many leading and trailing zeros.  
   * *Alternative:* Use a simple delta encoding if Gorilla XOR is too complex for the initial version.  
4. **Run-Length Encoding (RLE):**  
   * The double-delta encoded timestamps are a prime candidate for RLE, as they will contain long runs of zeros. Implement a simple RLE for these integer arrays.  
5. Package the series metadata and the now-compressed column data into a final structure and serialize it to a binary file (metrics.compressed.bin).  
6. Calculate and print the file size.

**Rationale:**

* **Pro:** This is where the dramatic (\>90%) storage reduction happens. We are no longer storing raw values but highly compressed representations of their changes.  
* **Counterpoint:** Computational cost. Both writing and reading now require CPU cycles to encode and decode the data. The data is completely opaque without the specific logic used to create it. This is a classic space-vs-time trade-off.

## **Phase 4: A Simple Custom Binary Format**

**Goal:** Formalize the compressed data into a simple, self-contained binary file format.

**Implementation (04\_custom\_binary\_format.py):**

1. Define a file structure:  
   * **File Header:** (e.g., 8 bytes for a magic number METRICS\!, 4 bytes for version 1).  
   * **Index Section:** Contains the series metadata (the "symbol table"). It should specify the byte offset where the data for each series begins.  
   * **Data Section:** Contiguous blocks of compressed data from Phase 3\.  
2. Write the script to pack this data together using Python's struct module for the header and index, followed by the raw compressed bytes for the data. The output is metrics.final.tsdb.  
3. Calculate and print the final size.

**Rationale:**

* **Pro:** Mimics how a real database file is laid out on disk. It's efficient to parse because you can read the index to find exactly where your desired data is without scanning the whole file.  
* **Counterpoint:** Maximum complexity. Any change to the format requires careful version management. It's completely non-portable without a dedicated reader.

## **Phase 5: Losing Precision for Longevity \- Downsampling**

**Goal:** Reduce data volume for long-term storage by aggregating high-resolution data into lower-resolution "rollups".

**Implementation (05\_downsampling\_storage.py):**

1. Read the generated high-resolution data.  
2. Define an aggregation interval (e.g., 5 minutes).  
3. For each time series, group data points into time buckets based on the interval.  
4. For each bucket, compute a set of aggregates. For example, for a cpu\_usage metric, you would generate several new aggregated series: cpu\_usage\_avg\_5m, cpu\_usage\_max\_5m, cpu\_usage\_count\_5m.  
5. Store these new, lower-resolution time series using the most efficient storage format from Phase 4\. This demonstrates the combined effect of compression and aggregation.  
6. Calculate and print the final file size, comparing it to the high-resolution data stored in the same format.

**Rationale:**

* **Pro:** The only viable strategy for affordable, long-term metric retention. Queries over long time ranges (e.g., "show me CPU usage for the last year") become dramatically faster as they process orders of magnitude fewer data points.  
* **Counterpoint:** This is a lossy process. You lose the ability to see intra-interval details. A 1-second spike in latency will be hidden if you only store a 1-minute average. This is why storing multiple aggregations like max and p99 is critical to retain visibility into outlier behavior.

## **Project Structure**

/metrics-storage-evolution  
|-- 00\_generate\_data.py  
|-- 01\_ndjson\_storage.py  
|-- 02\_columnar\_storage.py  
|-- 03\_compressed\_columnar.py  
|-- 04\_custom\_binary\_format.py  
|-- 05\_downsampling\_storage.py  
|-- main.py  
|-- README.md  
|-- /lib  
|   |-- encoders.py       \# (For delta, RLE, etc.)  
|   |-- data\_generator.py  
|-- /output  
|   |-- metrics.ndjson  
|   |-- metrics.columnar.msgpack  
|   |-- ...

The main.py script will orchestrate the process:

1. Call the data generator.  
2. Call script 01, passing the data, and report results.  
3. Call script 02, passing the data, and report results.  
4. ...and so on, up to and including the new downsampling phase.  
5. Finally, print a summary table comparing all methods.