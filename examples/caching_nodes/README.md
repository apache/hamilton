# Caching

There are four general approaches to caching in Apache Hamilton.

1. You do it yourself outside of Apache Hamilton and use the [`overrides`](https://hamilton.apache.org/reference/drivers/#short-circuiting-some-dag-computation) argument in `.execute/.materialize(..., overrides={...})` to inject pre-computed values into the graph. That is, you run your code, save the things you want, and then you load them and inject them using `overrides=`. TODO: show example.
2. You use the data savers & data loaders. This is similar to the above, but instead you use the [Data Savers & Data Loaders (i.e. materializers)](https://hamilton.apache.org/reference/io/available-data-adapters/) to save & then load and inject data in. TODO: show example.
3. You use the `CachingGraphAdapter`, which requires you to tag functions to cache along with the serialization format.
4. You use the `DiskCacheAdapter`, which uses the `diskcache` library to store the results on disk.

All approaches have their sweet spots and trade-offs. We invite you play with them and provide feedback on which one you prefer.
