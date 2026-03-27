from ahp_analyzer import AHPAnalyzer
from exporters import ExcelExporter, PlantUMLExporter


if __name__ == "__main__":
    yaml_path = "in/hierarchy.yaml"  # Update path if needed
    excel_path = "out/AHP_Results_Final.xlsx"
    csv_path = "out/AHP_Global_Weights_Final.csv"
    uml_path = "out/AHP_Risks_Mindmap.puml"

    analyzer = AHPAnalyzer()
    hierarchy = analyzer.load_hierarchy(yaml_path)
    flat_data = analyzer.build_comparison_matrices(hierarchy)
    local_weights_by_path = analyzer.calculate_local_weights_by_path(flat_data)
    global_weights = analyzer.propagate_global_weights(local_weights_by_path)

    ExcelExporter(local_weights_by_path, global_weights).save_results_to_excel_and_csv(excel_path, csv_path)
    PlantUMLExporter(hierarchy, global_weights).generate(uml_path)
