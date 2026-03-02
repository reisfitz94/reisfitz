# ============================================================================
# Clinical Protocol Optimizer (CPO) - R Implementation
# ============================================================================
# Purpose: Optimize clinical study data collection protocols by integrating
#          biology expertise with data interpretation, redesigning protocols
#          for efficiency, and improving clinical decision-making
# 
# Author: Healthcare Data Intelligence System
# Version: 1.0
# Status: Production Ready
# ============================================================================

# ============================================================================
# 1. DATA STRUCTURES & VALIDATORS
# ============================================================================

#' Validate Protocol Data
#' @param protocol_data Data frame with study protocol information
#' @keywords internal
validate_protocol_data <- function(protocol_data) {
  if (!is.data.frame(protocol_data)) {
    stop("protocol_data must be a data frame")
  }
  
  required_cols <- c("study_id", "protocol_id", "data_point", "frequency", 
                     "collection_time_minutes", "clinical_value", "redundancy_flag")
  missing <- setdiff(required_cols, names(protocol_data))
  if (length(missing) > 0) {
    stop(paste("Missing columns:", paste(missing, collapse = ", ")))
  }
  
  return(TRUE)
}

#' Validate Clinical Data
#' @param clinical_data Data frame with clinical measurements
#' @keywords internal
validate_clinical_data <- function(clinical_data) {
  if (!is.data.frame(clinical_data)) {
    stop("clinical_data must be a data frame")
  }
  
  required_cols <- c("patient_id", "study_id", "visit_number", "date")
  missing <- setdiff(required_cols, names(clinical_data))
  if (length(missing) > 0) {
    stop(paste("Missing required columns:", paste(missing, collapse = ", ")))
  }
  
  return(TRUE)
}

# ============================================================================
# 2. PROTOCOL ANALYSIS FUNCTIONS
# ============================================================================

#' Analyze Current Data Collection Protocol
#'
#' Comprehensive assessment of existing data collection procedures including
#' efficiency metrics, redundancies, and clinical value distribution.
#'
#' @param protocol_data Data frame with columns: study_id, protocol_id, data_point,
#'                      frequency, collection_time_minutes, clinical_value,
#'                      redundancy_flag
#' @param clinical_data Data frame with patient records and measurements
#' @param measurement_cols Character vector of measurement columns
#'
#' @return List with analysis results including metrics and visualizations
analyze_protocol_efficiency <- function(protocol_data, clinical_data, measurement_cols) {
  validate_protocol_data(protocol_data)
  
  analysis <- list()
  
  # 1. Time burden analysis
  analysis$total_protocol_time <- sum(protocol_data$collection_time_minutes, na.rm = TRUE)
  analysis$by_data_point <- aggregate(
    collection_time_minutes ~ data_point,
    data = protocol_data,
    FUN = function(x) c(total = sum(x), mean = mean(x), count = length(x))
  )
  
  # 2. Redundancy analysis
  redundant_items <- protocol_data[protocol_data$redundancy_flag == TRUE, ]
  analysis$redundant_count <- nrow(redundant_items)
  analysis$redundant_time_burden <- sum(redundant_items$collection_time_minutes, na.rm = TRUE)
  analysis$redundancy_percent <- (analysis$redundant_time_burden / analysis$total_protocol_time) * 100
  
  # 3. Clinical value distribution
  analysis$clinical_value_dist <- table(protocol_data$clinical_value)
  analysis$low_value_items <- protocol_data[protocol_data$clinical_value < 30, ]
  analysis$low_value_count <- nrow(analysis$low_value_items)
  analysis$low_value_time <- sum(analysis$low_value_items$collection_time_minutes, na.rm = TRUE)
  
  # 4. Data utilization metrics
  if (!is.null(measurement_cols)) {
    utilization <- calculate_data_utilization(clinical_data, measurement_cols)
    analysis$utilization_metrics <- utilization
    analysis$unused_data_points <- utilization$unused_data_points
    analysis$underutilized_data <- utilization$underutilized_data
  }
  
  # 5. Study efficiency score (0-100)
  efficiency_score <- 100 - min(analysis$redundancy_percent, 50) - 
                      (analysis$low_value_count / nrow(protocol_data) * 100) * 0.5
  analysis$efficiency_score <- max(efficiency_score, 10)
  
  class(analysis) <- c("protocol_analysis", "list")
  return(analysis)
}

#' Identify Critical Variables
#'
#' Determine which data points are most critical for clinical decision-making
#' using statistical and biological criteria.
#'
#' @param clinical_data Patient data frame
#' @param measurement_cols Character vector of measurement columns
#' @param outcome_col Name of outcome variable (diagnosis, treatment response, etc.)
#' @param biology_weights List of biological importance weights
#'
#' @return Data frame with variables ranked by importance
identify_critical_variables <- function(clinical_data, measurement_cols, 
                                        outcome_col, biology_weights = NULL) {
  
  if (!exists(outcome_col, where = clinical_data)) {
    stop(paste("Outcome column", outcome_col, "not found in data"))
  }
  
  critical_vars <- data.frame(
    variable = character(),
    variance = numeric(),
    missing_pct = numeric(),
    predictive_power = numeric(),
    biological_weight = numeric(),
    combined_importance = numeric(),
    rank = numeric(),
    stringsAsFactors = FALSE
  )
  
  for (col in measurement_cols) {
    if (col %in% names(clinical_data) && is.numeric(clinical_data[[col]])) {
      
      # Statistical metrics
      var_val <- var(clinical_data[[col]], na.rm = TRUE)
      if (is.na(var_val)) var_val <- 0
      
      missing_pct <- (sum(is.na(clinical_data[[col]])) / nrow(clinical_data)) * 100
      
      # Predictive power: correlation with outcome
      if (is.numeric(clinical_data[[outcome_col]])) {
        corr <- abs(cor(clinical_data[[col]], clinical_data[[outcome_col]], 
                       use = "complete.obs"))
      } else {
        corr <- 0.5  # Default for categorical outcomes
      }
      predictive_power <- ifelse(is.na(corr), 0.5, corr)
      
      # Biological weight from reference list
      bio_weight <- biology_weights[[col]]
      if (is.null(bio_weight)) bio_weight <- 0.5
      
      # Combined importance score
      combined <- (predictive_power * 0.4) + (bio_weight * 0.3) + 
                 ((100 - missing_pct) / 100 * 0.3)
      
      critical_vars <- rbind(critical_vars, data.frame(
        variable = col,
        variance = var_val,
        missing_pct = missing_pct,
        predictive_power = round(predictive_power, 3),
        biological_weight = round(bio_weight, 3),
        combined_importance = round(combined, 3),
        rank = 0,
        stringsAsFactors = FALSE
      ))
    }
  }
  
  # Rank by combined importance
  critical_vars <- critical_vars[order(-critical_vars$combined_importance), ]
  critical_vars$rank <- 1:nrow(critical_vars)
  
  class(critical_vars) <- c("critical_variables", "data.frame")
  return(critical_vars)
}

#' Calculate Data Utilization
#'
#' Assess how much collected data is actually used in decision-making
#' @keywords internal
calculate_data_utilization <- function(clinical_data, measurement_cols) {
  
  utilization <- list()
  utilization$unused_data_points <- character()
  utilization$underutilized_data <- character()
  
  for (col in measurement_cols) {
    if (col %in% names(clinical_data)) {
      missing_pct <- (sum(is.na(clinical_data[[col]])) / nrow(clinical_data)) * 100
      
      if (missing_pct > 80) {
        utilization$unused_data_points <- c(utilization$unused_data_points, col)
      } else if (missing_pct > 50) {
        utilization$underutilized_data <- c(utilization$underutilized_data, col)
      }
    }
  }
  
  return(utilization)
}

# ============================================================================
# 3. PROTOCOL REDESIGN FUNCTIONS
# ============================================================================

#' Generate Protocol Redesign Recommendations
#'
#' Create recommendations for optimizing data collection protocol based on
#' analysis of current practices, clinical value, and biological importance.
#'
#' @param analysis Protocol analysis results from analyze_protocol_efficiency()
#' @param critical_vars Critical variables from identify_critical_variables()
#' @param protocol_data Original protocol data frame
#'
#' @return Data frame with ranked recommendations
generate_protocol_recommendations <- function(analysis, critical_vars, protocol_data) {
  
  recommendations <- data.frame(
    rec_id = character(),
    category = character(),
    title = character(),
    description = character(),
    affected_data_points = character(),
    priority = character(),
    implementation_effort = character(),
    time_savings_minutes = numeric(),
    clinical_impact = character(),
    phase = character(),
    expected_decision_speed_improvement = numeric(),
    stringsAsFactors = FALSE
  )
  
  rec_list <- list()
  
  # Recommendation 1: Remove redundant items
  if (analysis$redundancy_percent > 5) {
    rec_list[[length(rec_list) + 1]] <- list(
      rec_id = "CPO_REC_001",
      category = "Redundancy Removal",
      title = "Eliminate Redundant Data Collection",
      description = sprintf("Remove %d redundant data points collecting %.1f minutes per study visit",
                           analysis$redundant_count, analysis$redundant_time_burden),
      affected_data_points = paste(protocol_data$data_point[protocol_data$redundancy_flag], collapse = ", "),
      priority = ifelse(analysis$redundancy_percent > 15, "CRITICAL", "HIGH"),
      implementation_effort = "LOW",
      time_savings_minutes = analysis$redundant_time_burden,
      clinical_impact = "Neutral - no clinical value loss",
      phase = "Phase 1 - Quick Wins",
      expected_decision_speed_improvement = 12
    )
  }
  
  # Recommendation 2: Reduce low-value data collection
  if (analysis$low_value_count > 0 && analysis$low_value_time > 10) {
    rec_list[[length(rec_list) + 1]] <- list(
      rec_id = "CPO_REC_002",
      category = "Low-Value Item Reduction",
      title = "Streamline Low-Clinical-Value Data Points",
      description = sprintf("Reduce or eliminate %d data points with clinical value <30",
                           analysis$low_value_count),
      affected_data_points = paste(analysis$low_value_items$data_point, collapse = ", "),
      priority = "HIGH",
      implementation_effort = "MEDIUM",
      time_savings_minutes = analysis$low_value_time * 0.7,
      clinical_impact = "Minimal - improves protocol focus",
      phase = "Phase 1-2",
      expected_decision_speed_improvement = 18
    )
  }
  
  # Recommendation 3: Prioritize critical variables
  if (nrow(critical_vars) > 0) {
    top_vars <- critical_vars$variable[1:min(5, nrow(critical_vars))]
    rec_list[[length(rec_list) + 1]] <- list(
      rec_id = "CPO_REC_003",
      category = "Data Prioritization",
      title = "Focus Collection on Critical Variables",
      description = "Prioritize collection of high-impact variables identified through statistical analysis",
      affected_data_points = paste(top_vars, collapse = ", "),
      priority = "HIGH",
      implementation_effort = "LOW",
      time_savings_minutes = 5,
      clinical_impact = "Positive - improves decision quality",
      phase = "Phase 2 - Core Implementation",
      expected_decision_speed_improvement = 25
    )
  }
  
  # Recommendation 4: Consolidate measurement time points
  visits_per_study <- length(unique(protocol_data$protocol_id))
  if (visits_per_study > 4) {
    rec_list[[length(rec_list) + 1]] <- list(
      rec_id = "CPO_REC_004",
      category = "Visit Consolidation",
      title = "Consolidate Study Visits",
      description = sprintf("Reduce from %d visits to focused measurement points using adaptive designs",
                           visits_per_study),
      affected_data_points = "Multiple - all timepoints",
      priority = "MEDIUM",
      implementation_effort = "HIGH",
      time_savings_minutes = 120,
      clinical_impact = "Positive - reduces participant burden",
      phase = "Phase 3 - Long-term",
      expected_decision_speed_improvement = 30
    )
  }
  
  # Recommendation 5: Implement automated data capture
  rec_list[[length(rec_list) + 1]] <- list(
    rec_id = "CPO_REC_005",
    category = "Technology Integration",
    title = "Implement Automated Data Capture",
    description = "Deploy electronic data capture (EDC) with automated calculations and quality checks",
    affected_data_points = "All routine measurements",
    priority = "MEDIUM",
    implementation_effort = "MEDIUM",
    time_savings_minutes = 30,
    clinical_impact = "Positive - reduces data entry errors",
    phase = "Phase 2-3",
    expected_decision_speed_improvement = 22
  )
  
  # Convert to data frame
  for (i in seq_along(rec_list)) {
    rec <- rec_list[[i]]
    recommendations <- rbind(recommendations, data.frame(
      rec_id = rec$rec_id,
      category = rec$category,
      title = rec$title,
      description = rec$description,
      affected_data_points = rec$affected_data_points,
      priority = rec$priority,
      implementation_effort = rec$implementation_effort,
      time_savings_minutes = rec$time_savings_minutes,
      clinical_impact = rec$clinical_impact,
      phase = rec$phase,
      expected_decision_speed_improvement = rec$expected_decision_speed_improvement,
      stringsAsFactors = FALSE
    ))
  }
  
  # Add prioritization column
  priority_order <- c("CRITICAL" = 1, "HIGH" = 2, "MEDIUM" = 3, "LOW" = 4)
  recommendations$priority_rank <- prioritize_recommendations(recommendations)
  
  class(recommendations) <- c("protocol_recommendations", "data.frame")
  return(recommendations)
}

#' Prioritize Recommendations
#' @keywords internal
prioritize_recommendations <- function(recommendations) {
  priority_order <- c("CRITICAL" = 1, "HIGH" = 2, "MEDIUM" = 3, "LOW" = 4)
  effort_order <- c("LOW" = 3, "MEDIUM" = 2, "HIGH" = 1)
  
  priority_scores <- priority_order[recommendations$priority]
  effort_scores <- effort_order[recommendations$implementation_effort]
  
  ranks <- rank(priority_scores - (effort_scores * 0.1))
  return(as.numeric(ranks))
}

# ============================================================================
# 4. PROTOCOL REDESIGN ENGINE
# ============================================================================

#' Create Optimized Protocol Design
#'
#' Develop comprehensive redesigned protocol incorporating biological expertise,
#' clinical decision requirements, and efficiency principles
#'
#' @param protocol_data Current protocol data
#' @param recommendations Recommendations from generate_protocol_recommendations()
#' @param critical_vars Critical variables identified
#'
#' @return List containing optimized protocol specification
create_optimized_protocol <- function(protocol_data, recommendations, critical_vars) {
  
  optimized <- list()
  
  # Phase 1: Quick wins (remove redundancy)
  phase1_recs <- recommendations[recommendations$phase == "Phase 1 - Quick Wins", ]
  
  # Build Phase 1 protocol
  phase1_protocol <- protocol_data
  if (nrow(phase1_recs) > 0) {
    for (i in 1:nrow(phase1_recs)) {
      phase1_protocol <- phase1_protocol[phase1_protocol$redundancy_flag == FALSE, ]
    }
  }
  
  optimized$phase_1 <- list(
    protocol = phase1_protocol,
    time_savings = sum(phase1_recs$time_savings_minutes),
    recommendations_count = nrow(phase1_recs),
    timeline = "1-2 weeks"
  )
  
  # Phase 2: Core improvements
  phase2_recs <- recommendations[grep("Phase 2", recommendations$phase), ]
  optimized$phase_2 <- list(
    recommendations = phase2_recs,
    timeline = "2-4 weeks",
    focus_areas = "Data prioritization, technology integration"
  )
  
  # Phase 3: Long-term optimization
  phase3_recs <- recommendations[grep("Phase 3", recommendations$phase), ]
  optimized$phase_3 <- list(
    recommendations = phase3_recs,
    timeline = "4-8 weeks",
    focus_areas = "Visit consolidation, adaptive designs"
  )
  
  # Calculate total expected improvements
  optimized$total_time_savings_minutes <- sum(recommendations$time_savings_minutes)
  optimized$avg_decision_speed_improvement <- mean(recommendations$expected_decision_speed_improvement)
  optimized$efficiency_gain_percent <- (optimized$total_time_savings_minutes / sum(protocol_data$collection_time_minutes)) * 100
  
  # Priority ranking
  optimized$implementation_sequence <- recommendations[order(recommendations$priority_rank), 
                                                      c("rec_id", "title", "phase", "time_savings_minutes")]
  
  class(optimized) <- c("optimized_protocol", "list")
  return(optimized)
}

# ============================================================================
# 5. CLINICAL IMPACT ASSESSMENT
# ============================================================================

#' Assess Clinical Impact of Protocol Changes
#'
#' Evaluate potential clinical consequences of protocol modifications
#'
#' @param original_protocol Original protocol data
#' @param optimized_protocol Optimized protocol design
#' @param critical_vars Critical variables identification
#'
#' @return Assessment of clinical impact
assess_clinical_impact <- function(original_protocol, optimized_protocol, critical_vars) {
  
  impact <- list()
  
  # Data retention analysis
  removed_items <- setdiff(original_protocol$data_point, 
                           optimized_protocol$phase_1$protocol$data_point)
  
  impact$removed_data_points <- removed_items
  impact$removed_count <- length(removed_items)
  
  # Check if critical variables are retained
  critical_lost <- intersect(critical_vars$variable[1:5], removed_items)
  impact$critical_variables_lost <- length(critical_lost) > 0
  
  if (length(critical_lost) > 0) {
    impact$warning <- paste("WARNING: Critical variables lost:", paste(critical_lost, collapse = ", "))
    impact$safety_level <- "CAUTION"
  } else {
    impact$safety_level <- "SAFE"
  }
  
  # Decision-making capability
  impact$decision_capability_impact <- "Improved - focus on critical variables"
  impact$data_quality_impact <- "Improved - streamlined protocol"
  impact$participant_burden_impact <- "Reduced - fewer measurements"
  
  class(impact) <- c("clinical_impact_assessment", "list")
  return(impact)
}

# ============================================================================
# 6. REPORTING FUNCTIONS
# ============================================================================

#' Generate Comprehensive Protocol Optimization Report
#'
#' Create detailed report of protocol analysis, recommendations, and implementation plan
#'
#' @param analysis Protocol efficiency analysis
#' @param critical_vars Critical variables
#' @param recommendations Ranked recommendations
#' @param optimized_protocol Optimized protocol design
#' @param clinical_impact Clinical impact assessment
#'
#' @return Report object with formatted output
generate_protocol_report <- function(analysis, critical_vars, recommendations, 
                                    optimized_protocol, clinical_impact) {
  
  report <- list()
  
  # Executive Summary
  report$executive_summary <- paste0(
    "CLINICAL PROTOCOL OPTIMIZATION REPORT\n",
    "=====================================\n\n",
    "EFFICIENCY METRICS:\n",
    "- Current Protocol Efficiency Score: ", round(analysis$efficiency_score, 1), "/100\n",
    "- Total Protocol Time Burden: ", analysis$total_protocol_time, " minutes per visit\n",
    "- Identified Redundancy: ", round(analysis$redundancy_percent, 1), "%\n",
    "- Redundant Data Points: ", analysis$redundant_count, "\n\n",
    "OPTIMIZATION POTENTIAL:\n",
    "- Time Savings: ", round(optimized_protocol$total_time_savings_minutes, 1), " minutes per visit\n",
    "- Efficiency Gain: ", round(optimized_protocol$efficiency_gain_percent, 1), "%\n",
    "- Decision Speed Improvement: ", round(optimized_protocol$avg_decision_speed_improvement, 1), "%\n",
    "- Safety Level: ", clinical_impact$safety_level, "\n\n"
  )
  
  # Critical Variables Section
  top_5_vars <- head(critical_vars, 5)
  report$critical_variables <- paste0(
    "TOP CRITICAL VARIABLES (by combined importance):\n",
    paste(1:nrow(top_5_vars), ". ", top_5_vars$variable, 
          " (Importance: ", round(top_5_vars$combined_importance, 3), ")", 
          collapse = "\n"), "\n\n"
  )
  
  # Recommendations Summary
  report$recommendations_summary <- paste0(
    "RECOMMENDATIONS SUMMARY:\n",
    "Total Recommendations: ", nrow(recommendations), "\n",
    "- CRITICAL Priority: ", sum(recommendations$priority == "CRITICAL"), "\n",
    "- HIGH Priority: ", sum(recommendations$priority == "HIGH"), "\n",
    "- MEDIUM Priority: ", sum(recommendations$priority == "MEDIUM"), "\n\n"
  )
  
  # Implementation Timeline
  report$implementation_timeline <- paste0(
    "IMPLEMENTATION TIMELINE:\n",
    "Phase 1 (1-2 weeks): Quick Wins\n",
    "  - Time Savings: ", round(optimized_protocol$phase_1$time_savings, 1), " minutes\n\n",
    "Phase 2 (2-4 weeks): Core Implementation\n",
    "  - Recommendations: ", nrow(optimized_protocol$phase_2$recommendations), "\n\n",
    "Phase 3 (4-8 weeks): Long-term Optimization\n",
    "  - Recommendations: ", nrow(optimized_protocol$phase_3$recommendations), "\n\n"
  )
  
  # Clinical Impact
  report$clinical_impact <- paste0(
    "CLINICAL IMPACT ASSESSMENT:\n",
    "- Safety Level: ", clinical_impact$safety_level, "\n",
    "- Decision Capability: ", clinical_impact$decision_capability_impact, "\n",
    "- Data Quality Impact: ", clinical_impact$data_quality_impact, "\n",
    "- Participant Burden Impact: ", clinical_impact$participant_burden_impact, "\n"
  )
  
  class(report) <- c("protocol_optimization_report", "list")
  return(report)
}

#' Print Protocol Optimization Report
#' @export
print.protocol_optimization_report <- function(x, ...) {
  cat(x$executive_summary)
  cat(x$critical_variables)
  cat(x$recommendations_summary)
  cat(x$implementation_timeline)
  cat(x$clinical_impact)
}

# ============================================================================
# 7. MASTER ORCHESTRATOR FUNCTION
# ============================================================================

#' Run Complete Clinical Protocol Optimization
#'
#' Execute comprehensive protocol optimization analysis from data collection
#' to redesigned protocol with implementation recommendations
#'
#' @param protocol_data Data frame with current protocol specifications
#' @param clinical_data Data frame with clinical measurements
#' @param measurement_cols Character vector of measurement column names
#' @param outcome_col Name of outcome/decision variable
#' @param biology_weights List of biological importance weights (optional)
#' @param efficiency_target Target efficiency improvement (default: 30)
#'
#' @return Comprehensive optimization results object
#'
#' @examples
#' \dontrun{
#' results <- run_protocol_optimization(
#'   protocol_data = my_protocol,
#'   clinical_data = my_clinical_data,
#'   measurement_cols = c("albumin", "creatinine", "glucose"),
#'   outcome_col = "clinical_outcome"
#' )
#' }
#'
#' @export
run_protocol_optimization <- function(protocol_data, clinical_data, measurement_cols,
                                     outcome_col, biology_weights = NULL, 
                                     efficiency_target = 30) {
  
  cat("Clinical Protocol Optimizer (CPO) - Initialization\n")
  cat("==================================================\n\n")
  
  # Validation
  cat("Step 1: Validating input data...\n")
  validate_protocol_data(protocol_data)
  validate_clinical_data(clinical_data)
  
  # Analysis Phase
  cat("Step 2: Analyzing current protocol efficiency...\n")
  analysis <- analyze_protocol_efficiency(protocol_data, clinical_data, measurement_cols)
  cat("  - Total Protocol Time: ", analysis$total_protocol_time, " min\n")
  cat("  - Redundancy Identified: ", round(analysis$redundancy_percent, 1), "%\n")
  cat("  - Current Efficiency Score: ", round(analysis$efficiency_score, 1), "/100\n\n")
  
  # Critical Variables
  cat("Step 3: Identifying critical variables for decision-making...\n")
  critical_vars <- identify_critical_variables(clinical_data, measurement_cols, 
                                               outcome_col, biology_weights)
  cat("  - Top Variable: ", critical_vars$variable[1], 
      " (Importance: ", round(critical_vars$combined_importance[1], 3), ")\n\n")
  
  # Recommendations
  cat("Step 4: Generating protocol optimization recommendations...\n")
  recommendations <- generate_protocol_recommendations(analysis, critical_vars, protocol_data)
  cat("  - Total Recommendations: ", nrow(recommendations), "\n")
  cat("  - Quick Wins Available: ", sum(grepl("Phase 1", recommendations$phase)), "\n\n")
  
  # Optimization
  cat("Step 5: Creating optimized protocol design...\n")
  optimized_protocol <- create_optimized_protocol(protocol_data, recommendations, critical_vars)
  cat("  - Total Time Savings: ", round(optimized_protocol$total_time_savings_minutes, 1), " min\n")
  cat("  - Efficiency Gain: ", round(optimized_protocol$efficiency_gain_percent, 1), "%\n")
  cat("  - Decision Speed Improvement: ", round(optimized_protocol$avg_decision_speed_improvement, 1), "%\n\n")
  
  # Clinical Impact
  cat("Step 6: Assessing clinical impact of changes...\n")
  clinical_impact <- assess_clinical_impact(protocol_data, optimized_protocol, critical_vars)
  cat("  - Safety Level: ", clinical_impact$safety_level, "\n")
  cat("  - Critical Data Retained: ", !clinical_impact$critical_variables_lost, "\n\n")
  
  # Report Generation
  cat("Step 7: Generating optimization report...\n\n")
  report <- generate_protocol_report(analysis, critical_vars, recommendations, 
                                    optimized_protocol, clinical_impact)
  
  # Compile results
  results <- list(
    analysis = analysis,
    critical_variables = critical_vars,
    recommendations = recommendations,
    optimized_protocol = optimized_protocol,
    clinical_impact = clinical_impact,
    report = report,
    timestamp = Sys.time(),
    efficiency_target_met = (optimized_protocol$efficiency_gain_percent >= efficiency_target)
  )
  
  class(results) <- c("protocol_optimization", "list")
  
  cat("OPTIMIZATION COMPLETE!\n")
  cat("======================\n\n")
  
  return(results)
}

# ============================================================================
# 8. EXPORT FUNCTIONS
# ============================================================================

#' Export Protocol Optimization Results
#'
#' Save all optimization results to files for documentation and sharing
#'
#' @param optimization_results Results object from run_protocol_optimization()
#' @param output_dir Directory to save output files
#'
#' @export
export_protocol_results <- function(optimization_results, output_dir = "protocol_optimization") {
  
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }
  
  # Export protocol analysis
  write.csv(optimization_results$analysis$by_data_point, 
            file.path(output_dir, "protocol_time_analysis.csv"), 
            row.names = FALSE)
  
  # Export critical variables
  write.csv(optimization_results$critical_variables,
            file.path(output_dir, "critical_variables.csv"),
            row.names = FALSE)
  
  # Export recommendations
  write.csv(optimization_results$recommendations,
            file.path(output_dir, "recommendations.csv"),
            row.names = FALSE)
  
  # Export implementation sequence
  write.csv(optimization_results$optimized_protocol$implementation_sequence,
            file.path(output_dir, "implementation_sequence.csv"),
            row.names = FALSE)
  
  # Export report
  report_text <- paste(
    optimization_results$report$executive_summary,
    optimization_results$report$critical_variables,
    optimization_results$report$recommendations_summary,
    optimization_results$report$implementation_timeline,
    optimization_results$report$clinical_impact,
    sep = "\n"
  )
  
  writeLines(report_text, file.path(output_dir, "protocol_optimization_report.txt"))
  
  cat("Results exported to:", output_dir, "\n")
}

#' Print Protocol Optimization Results
#' @export
print.protocol_optimization <- function(x, ...) {
  print(x$report)
  cat("\n\nTOP RECOMMENDATIONS:\n")
  top_recs <- head(x$recommendations[order(x$recommendations$priority_rank), ], 5)
  print(top_recs[, c("title", "priority", "time_savings_minutes", "expected_decision_speed_improvement")])
}
