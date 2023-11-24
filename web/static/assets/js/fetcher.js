// Function to fetch data from the API
function getAirlineColor(airlineName) {
  // Define an object mapping top low-cost airlines to logo hex colors
  const lowCostAirlineColors = {
    "Ryanair": "info",
    "EasyJet": "warning",
    "Wizz Air": "primary",
    // Add more low-cost airlines as needed
  };

  // Check if the airline name is in the list, return the color, otherwise return grey
  return lowCostAirlineColors[airlineName] || "secondary"; // Default to grey if not found
}

// Function to fetch data from the API
async function fetchData(month) {
  try {
    const response = await fetch(`/get_flights?month=${month}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

async function getAvailableMonths() {
  try {
    const response = await fetch(`/flight/get_available_months`);
    return await response.json()
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

function generateFlightsDiv(month) {
  return `
    <div class="row mt-4">
      <div class="table align-items-center mb-0">
        <div class="card ">
          <div class="card-header pb-0 p-3">
            <div class="d-flex justify-content-between">
              <h6 class="mb-2" id="${month}-flights-title"></h6>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table align-items-center flight-table" id="${month}-flights">
                <tbody>
                </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Function to append the generated HTML under a div with id "tables"
function appendCheapestFlightHTML(month) {
  const tablesDiv = document.getElementById("tables");
  if (tablesDiv) {
    tablesDiv.innerHTML += generateFlightsDiv(month);
  } else {
    console.error('Div with id "tables" not found.');
  }
}

// Function to dynamically create rows in the table
async function createTableRows(month, tableId) {
  const table = document.getElementById(tableId);
  const tableBody = table.querySelector('tbody');
  const tableTitle = document.getElementById(tableId + "-title");

  // Fetch data from the API
  const apiData = await fetchData(month);
  tableTitle.innerHTML = apiData[0] + " Flights"

  // Iterate through the data and create rows
  apiData[1].forEach((element) => {
    const row = tableBody.insertRow();

    // Column 1: Country
    const cell1 = row.insertCell(0);
    cell1.style.width = "20%"
    cell1.innerHTML = `
      <div class="d-flex px-2 py-1 align-items-center">
        <div>
          <img src="${element['flag']}" alt="Country flag">
        </div>
        <div class="ms-4">
          <p class="text-xs font-weight-bold mb-0">Destination:</p>
          <h6 class="text-sm mb-0">${element['destination']}</h6>
        </div>
      </div>
    `;

    // Column 2: Departure Date
    const cell2 = row.insertCell(1);
    cell2.style.width = "20%"
    cell2.innerHTML = `
      <div class="text-center">
        <p class="text-xs font-weight-bold mb-0">Departure Date</p>
        <h6 class="text-sm mb-0">${element['departureDate']}</h6>
      </div>
    `;

    // Column 3: Arrival Date
    const cell3 = row.insertCell(2);
    cell3.style.width = "20%"
    cell3.innerHTML = `
      <div class="text-center">
        <p class="text-xs font-weight-bold mb-0">Arrival Date</p>
        <h6 class="text-sm mb-0">${element['arrivalDate']}</h6>
      </div>
    `;

    // Column 4: Price
    const cell4 = row.insertCell(3);
    cell4.style.width = "10%"
    cell4.innerHTML = `
      <div class="text-center">
        <p class="text-xs font-weight-bold mb-0">Price:</p>
        <h6 class="text-sm mb-0">${element['price']} <span>&#8362;</span></h6>
      </div>
    `;

    // Column 5: Members Price
    const cell5 = row.insertCell(4);
    cell5.style.width = "10%"
    cell5.innerHTML = `
      <div class="text-center">
        <p class="text-xs font-weight-bold mb-0">Members Price:</p>
        <h6 class="text-sm mb-0">${element['membersPrice']} <span>&#8362;</span></h6>
      </div>
    `;

    // Column 6: Airlines
    const cell6 = row.insertCell(5);
    cell6.style.width = "20%"
    const airlinesHTML = createAirlinesHTML(element['airlines']);
    cell6.innerHTML = `
      <div class="text-center">
        <p class="text-xs font-weight-bold mb-0">Airlines:</p>
        <h6 class="text-sm mb-0">${airlinesHTML}</h6>
      </div>
    `;
  });
}

// Function to create HTML for Airlines section based on element.airlines
function createAirlinesHTML(airlines) {
  let airlinesHTML = '';

  if (airlines['round'][0]) {
    airlinesHTML += `<a href="${airlines['round'][1]}" class="badge badge-sm bg-gradient-${getAirlineColor(airlines['round'][0])}">${airlines['round'][0]}</a> `;
  } else {
    if (airlines['departure'][0]) {
      airlinesHTML += `<a href="${airlines['departure'][1]}" class="badge badge-sm bg-gradient-${getAirlineColor(airlines['departure'][0])}">${airlines['departure'][0]}</a> `;
    }
    if (airlines['arrival'][0]) {
      airlinesHTML += `<a href="${airlines['arrival'][1]}" class="badge badge-sm bg-gradient-${getAirlineColor(airlines['arrival'][0])}">${airlines['arrival'][0]}</a> `;
    }
  }

  return airlinesHTML;
}

// Function to set up filter inputs for a table
// Function to set up filters for each column
function setupFilters(tableId) {
  const table = document.getElementById("filter-table");
  const headerRow = table.querySelector('thead tr');

  if (headerRow) {
    Array.from(headerRow.cells).forEach((cell, index) => {
      const filterInput = document.createElement('input');
      filterInput.type = 'text';
      filterInput.placeholder = 'Filter';
      filterInput.className = 'form-control';
      filterInput.addEventListener('input', () => {
        filterTables();
      });

      cell.appendChild(filterInput);
    });
  }
}

// Function to filter the table based on user input
function filterTables() {
  const tables = document.getElementsByClassName("flight-table");
  const filterInputs = Array.from(document.getElementById("filter-table").querySelectorAll('thead input'));

  for (const table of tables) {
    const rows = table.querySelectorAll('tbody tr');
    Array.from(rows).forEach(row => {
      let isVisible = true;

      filterInputs.forEach((filterInput, index) => {
        const cell = row.cells[index];
        const cellValue = cell.textContent.toLowerCase();
        const filterValue = filterInput.value.toLowerCase();
        isVisible = isVisible && cellValue.includes(filterValue);
      });

      row.style.display = isVisible ? '' : 'none';
    });
  }

}


// Function to create tables for each available month
async function createTables() {
  const months = await getAvailableMonths();
  months.forEach(month => {
    appendCheapestFlightHTML(month);
  })
  setupFilters();
  for (const month of months) {
    await createTableRows(month, `${month}-flights`);
  }
}

// Call the function to create table rows when the page loads
document.addEventListener('DOMContentLoaded', createTables);
