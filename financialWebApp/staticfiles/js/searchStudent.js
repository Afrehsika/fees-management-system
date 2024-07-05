const searchField = document.querySelector("#searchField");
const tableOutput = document.querySelector(".table-output");
const appTable = document.querySelector(".app-table");
const paginationContainer = document.querySelector(".pagination-container");
const tbody = document.querySelector(".table-body");

tableOutput.style.display = "none";

searchField.addEventListener("keyup", (e) => {
    const searchValue = e.target.value;

    if (searchValue.trim().length > 0) {
        paginationContainer.style.display = "none";
        tbody.innerHTML = "";

        fetch("/search-student", {
            body: JSON.stringify({ searchText: searchValue }),
            method: "POST",
        })
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                appTable.style.display = "none";
                tableOutput.style.display = "block";

                if (data.length === 0) {
                    tableOutput.innerHTML = "<h1>No Results Found</h1>";
                } else {
                    data.forEach((item) => {
                        tbody.innerHTML += `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.student_id}</td>
                                <td>${item.index_number}</td>
                                <td>${item.level}</td>
                                <td>GH&#8373; ${item.balance}</td> 
                                <td>GH&#8373; ${item.total_fees}</td> 
                                <td>GH&#8373; ${item.total_paid}</td>
                                <td>
                                <a href="/edit_students/${item.name}" class="btn btn-info btn-sm">Edit</a>
                                </td>
                            </tr>
                        `;
                    });
                }
            });
    } else {
        tableOutput.style.display = "none";
        appTable.style.display = "block";
        paginationContainer.style.display = "block";
    }
});
