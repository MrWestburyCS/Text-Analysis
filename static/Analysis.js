document.addEventListener("DOMContentLoaded", () => {
  const inputText = document.getElementById("inputText");
  const analyzeButton = document.getElementById("analyzeButton");
  const resultsOutput = document.getElementById("resultsOutput");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const errorDisplay = document.getElementById("errorDisplay");
  const checkboxContainer = document.getElementById("checkboxContainer"); // Get checkbox container

  const clearButton = document.getElementById("clearButton");
  const sampleButton = document.getElementById("sampleButton");
  const filterToggle = document.getElementById("filterToggle");
  const checkboxGrid = document.getElementById("checkboxContainer");
  const filterToggleIcon = document.querySelector(".filter-toggle");
  // --- Global state for results and filters ---
  let currentAnalysisData = null; // Store { originalText: '...', findings: [...] }
  let currentFilterState = {};

  // --- Initial population of filter state ---
  function updateFilterState() {
    currentFilterState = {};
    const checkboxes = checkboxContainer.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
      currentFilterState[cb.value] = cb.checked;
    });
    // console.log("Filter state updated:", currentFilterState); // For debugging
  }

  analyzeButton.addEventListener("click", async () => {
    const textToAnalyze = inputText.value;
    if (!textToAnalyze.trim()) {
      showError("Please enter some text to analyze.");
      return;
    }

    resultsOutput.innerHTML = "<p>Analysis results will appear here.</p>";
    hideError();
    loadingIndicator.style.display = "block";
    analyzeButton.disabled = true;
    currentAnalysisData = null; // Clear previous results

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToAnalyze }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMsg = data.error || `HTTP error! Status: ${response.status}`;
        if (data.errors && data.errors.length > 0) {
            errorMsg += ` Details: ${data.errors.join("; ")}`;
        }
        throw new Error(errorMsg);
      }

      const figures = data.figures_of_speech || [];
      const pos = data.parts_of_speech || [];
      const analysisErrors = data.errors || [];

      if (analysisErrors.length > 0) {
          showError(`Note: Some analysis steps encountered issues: ${analysisErrors.join("; ")}`);
      }

      const allFindings = [...figures, ...pos];

      // Store results globally
      currentAnalysisData = {
          originalText: textToAnalyze,
          findings: allFindings
      };

      // Update filter state from checkboxes (in case they were changed before analysis)
      updateFilterState();

      // Apply initial highlighting based on current filters
      applyHighlighting();

      if (allFindings.length === 0 && analysisErrors.length === 0) {
        resultsOutput.innerHTML = "<p>No specific items were identified.</p>";
      } else if (allFindings.length === 0 && analysisErrors.length > 0) {
         resultsOutput.innerHTML = "<p>Analysis complete, but no items found or partial errors occurred.</p>";
      }


    } catch (error) {
      console.error("Analysis Error:", error);
      showError(`Analysis failed: ${error.message}`);
      resultsOutput.innerHTML = "<p>An error occurred. Please try again.</p>";
      currentAnalysisData = null; // Clear data on error
    } finally {
      loadingIndicator.style.display = "none";
      analyzeButton.disabled = false;
    }
  });

  // --- Checkbox Change Handler ---
  checkboxContainer.addEventListener('change', (event) => {
      if (event.target.type === 'checkbox') {
          updateFilterState(); // Update the global filter state
          // Re-apply highlighting with the new filter state if data exists
          if (currentAnalysisData) {
              applyHighlighting();
          }
      }
  });


  function applyHighlighting() {
      if (!currentAnalysisData) {
          resultsOutput.innerHTML = "<p>No analysis data available to display.</p>";
          return;
      }

      const { originalText, findings } = currentAnalysisData;
      let highlightedHtml = escapeHtml(originalText);
      let itemsHighlighted = 0;


      const sortedFindings = [...findings].sort((a, b) => b.text.length - a.text.length);

      sortedFindings.forEach((finding) => {
          // Skip if text is missing or empty
          if (!finding.text || finding.text.trim() === "") return;

          // *** NEW: Check filter state ***
          if (!currentFilterState[finding.type]) {
              return; // Skip this finding if its type is unchecked
          }

          const escapedFindingText = escapeHtml(finding.text);
          const className = finding.type; // Use the type directly as class name
          // Format tooltip text nicely (e.g., 'proper_noun' -> 'Proper Noun')
          const tooltipText = finding.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

          // Regex for replacement (same as before)
          const regex = new RegExp(
              `(?<![\\w\\-])(${escapeRegExp(escapedFindingText)})(?![\\w\\-])`,
              "g"
          );

          let replaced = false;
          highlightedHtml = highlightedHtml.replace(regex, (match, p1) => {
              // Basic check to avoid re-wrapping span inside span.
              // This is complex. A simpler check might be to see if the match
              // is already immediately preceded by '>' or followed by '<'.
              // A truly robust solution requires DOM parsing, which is overkill here.
              // Let's assume simple replacement works for most cases.
              replaced = true;
              return `<span class="${className}" data-tooltip="${tooltipText}">${p1}</span>`;
          });
          if(replaced) {
              itemsHighlighted++;
          }
      });

      resultsOutput.innerHTML = highlightedHtml;

      if (itemsHighlighted === 0 && findings.length > 0) {
          resultsOutput.innerHTML += "<p><small>(No items visible with current filters)</small></p>";
      } else if (itemsHighlighted === 0 && findings.length === 0) {
           // Handled by the analyze button logic already
      }
  }



  function showError(message) {
    if (errorDisplay.style.display === 'block' && errorDisplay.textContent) {
        errorDisplay.textContent += ` | ${message}`;
    } else {
        errorDisplay.textContent = message;
    }
    errorDisplay.style.display = "block";
  }

  function hideError() {
    errorDisplay.style.display = "none";
    errorDisplay.textContent = "";
  }

  function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  updateFilterState(); 

  clearButton.addEventListener("click", () => {
    inputText.value = "";
    resultsOutput.innerHTML = "<p>Analysis results will appear here.</p>";
    hideError();
  });
  
  sampleButton.addEventListener("click", () => {
    inputText.value = "The old man was as stubborn as a mule. His heart was made of stone, but his words flowed like honey. The bright sun painted the sky with brilliant colors, while the trees danced in the gentle breeze. Life is a journey that takes unexpected turns.";
  });
  
  let filtersCollapsed = false;
  filterToggle.addEventListener("click", () => {
    filtersCollapsed = !filtersCollapsed;
    
    if (filtersCollapsed) {
      checkboxGrid.classList.add("collapsed");
      filterToggleIcon.classList.add("collapsed");
    } else {
      checkboxGrid.classList.remove("collapsed");
      filterToggleIcon.classList.remove("collapsed");
    }
  });
});
