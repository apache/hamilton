import analysis

from hamilton import driver


def main():
    hamilton_driver = driver.Builder().with_modules(analysis).build()
    hamilton_driver.display_all_functions("all_functions.png", orient="TB")

    inputs = dict(
        pdl_file="pdl_data.json",
        stock_file="stock_data.json",
        rounds_selection=["series_a", "series_b", "series_c", "series_d"],
    )

    final_vars = [
        "n_company_by_funding_stage",
        "augmented_company_info",
    ]

    results = hamilton_driver.execute(final_vars, inputs=inputs)
    print(f"Successfully computed the nodes: {list(results.keys())}")
    print(results["augmented_company_info"].head())

    # add code to store results
    # ref: https://hamilton.apache.org/concepts/materialization/


if __name__ == "__main__":
    main()
