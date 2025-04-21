document.addEventListener("DOMContentLoaded", function () {
    // Handle registration
    const signupForm = document.querySelector("#signup-form");
    const registerMessageBox = document.querySelector("#registerMessage");
    if (signupForm) {
        signupForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            let formData = new FormData(this);
            registerMessageBox.textContent = "";
            registerMessageBox.classList.remove("text-red-500", "text-green-500");

            fetch("/register", {
                method: "POST",
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                console.log("Server Response:", data);
                registerMessageBox.textContent = data.message;
                
                if (data.success) {
                    registerMessageBox.classList.add("text-green-500");
                    setTimeout(() => {
                        window.location.href = "/login";
                    }, 1000);
                } else {
                    registerMessageBox.classList.add("text-red-500");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                registerMessageBox.textContent = "Unexpected error. Try again later!";
                registerMessageBox.classList.add("text-red-500");
            });
        });
    }

    // Handle login
    const loginForm = document.querySelector("#login-form");
    const loginMessageBox = document.querySelector("#loginMessage");
    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            let formData = new FormData(this);
            loginMessageBox.textContent = "";
            loginMessageBox.classList.remove("text-red-500", "text-green-500");

            fetch("/login", {
                method: "POST",
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                console.log("Server Response:", data);
                loginMessageBox.textContent = data.message;
                
                if (data.success) {
                    loginMessageBox.classList.add("text-green-500");
                    setTimeout(() => {
                        window.location.href = "/";
                    }, 1000);
                } else {
                    loginMessageBox.classList.add("text-red-500");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                loginMessageBox.textContent = "Unexpected error. Try again later!";
                loginMessageBox.classList.add("text-red-500");
            });
        });
    }
});

// handle modal  toggle
document.addEventListener("DOMContentLoaded", function () {
    const profileButtonDesktop = document.getElementById("profile-btn"); // Desktop button
    const profileButtonMobile = document.getElementById("profile-btn-mobile"); // Mobile button
    const profileModalDesktop = document.getElementById("profile-modal"); // Desktop modal
    const profileModalMobile = document.getElementById("profile-modal-mobile"); // Mobile modal

    function toggleModal(modal) {
        modal.classList.toggle("hidden");
    }

    if (profileButtonDesktop) {
        profileButtonDesktop.addEventListener("click", function (event) {
            event.stopPropagation();
            toggleModal(profileModalDesktop);
        });
    }

    if (profileButtonMobile) {
        profileButtonMobile.addEventListener("click", function (event) {
            event.stopPropagation();
            toggleModal(profileModalMobile);
        });
    }

    // Close modals when clicking outside
    document.addEventListener("click", function (event) {
        if (!profileButtonDesktop.contains(event.target) && !profileModalDesktop.contains(event.target)) {
            profileModalDesktop.classList.add("hidden");
        }
        if (!profileButtonMobile.contains(event.target) && !profileModalMobile.contains(event.target)) {
            profileModalMobile.classList.add("hidden");
        }
    });
});


// prompt login for bookmark if not signed in
function promptLogin() {
    if (window.innerWidth < 768) {
        window.location.href = "/login";  // Redirect to login page on mobile
    } else {
        document.dispatchEvent(new Event('toggleSignup')); // Open the login modal on desktop
    }
}

// handle bookmark toggle
function toggleBookmark(event, button) {
    event.preventDefault();
    event.stopPropagation();

    const icon = button.querySelector("svg");
    const recipeId = button.getAttribute("data-recipe-id");
    const title = button.getAttribute("data-recipe-title");
    const image = button.getAttribute("data-recipe-image");

    if (!recipeId || !title || !image){
        console.log("Error: recipe data missing!");
        return;
    }

    //get csrf token frlom meta tag
    const csrfToken =document.querySelector("meta[name='csrf-token']").getAttribute("content");

    const isBookmarked = icon.getAttribute("fill") === "#1e293b";
    if (isBookmarked) {
        icon.setAttribute("fill", "none");
        icon.setAttribute("stroke", "currentColor");
        button.classList.add("text-gray-500");
        button.classList.remove("text-[#1e293b]");
    }else{
        icon.setAttribute("fill", "#1e293b");
        icon.setAttribute("stroke", "none");
        button.classList.add("text-[#1e293b]");
        button.classList.remove("text-gray-500");
    }

    console.log(`Sending bookmark request: RecipeID=${recipeId}, CSRF=${csrfToken}`);

    fetch("/bookmark", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `recipe_id=${encodeURIComponent(recipeId)}&title=${encodeURIComponent(title)}&image=${encodeURIComponent(image)}&csrf_token=${csrfToken}`
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response received: ", data);

        if (!data.success) {
            alert(data.message);

            if (isBookmarked) {
                icon.setAttribute("fill", "#1e293b");
                icon.setAttribute("stroke", "none");
                button.classList.add("text-[#1e293b]");
                button.classList.remove("text-gray-500");
            } else {
                icon.setAttribute("fill", "none");
                icon.setAttribute("stroke", "currentColor");
                button.classList.add("text-gray-500");
                button.classList.remove("text-[#1e293b]");
            }
        }
    })
    .catch(error => {
        console.error("Fetch Error: ", error);

        if (isBookmarked) {
            icon.setAttribute("fill", "#1e293b");
            icon.setAttribute("stroke", "none");
            button.classList.add("text-[#1e293b]");
            button.classList.remove("text-gray-500");
        } else {
            icon.setAttribute("fill", "none");
            icon.setAttribute("stroke", "currentColor");
            button.classList.add("text-gray-500");
            button.classList.remove("text-[#1e293b]");
        }
    });
}

// delete bookmarks
function deleteBookmark(button) {
    const recipeId = button.getAttribute("data-recipe-id");
    const csrfToken =document.querySelector("meta[name='csrf-token']").getAttribute("content");

    if (!recipeId) {
        console.error("Error: Missing recipe ID");
        return;
    }

    console.log(`Deleting bookmark: RecipeID=${recipeId}`);


    fetch("/bookmark/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `recipe_id=${encodeURIComponent(recipeId)}&csrf_token=${csrfToken}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Bookmark removed")
            // Remove the bookmark from the UI
            const card = button.closest(".recipe-card");
            if (card) {
                card.style.opacity = "0";
                setTimeout(() => {
                    card.remove();
                }, 300);
            }

            const bookmarkButton = document.querySelector(`[data-recipe-id="${recipeId}"]`);
            if (bookmarkButton) {
                const icon = bookmarkButton.querySelector("svg");
                icon.setAttribute("fill", "none");
                icon.setAttribute("stroke", "currentColor");
                bookmarkButton.classList.add("text-gray-500");
                bookmarkButton.classList.remove("text-[#1e293b]");
            }
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("❌ Fetch Error:", error);
    });
}

// search auto-suggestion logic
function fetchAutoSuggestions(inputId, resultsId) {
    const query = document.getElementById(inputId).value.trim();
    const resultsContainer = document.getElementById(resultsId);
    
    if (query.length < 2) {
        resultsContainer.classList.add("hidden");
        return;
    }

    fetch(`/autocomplete?query=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch suggestions");
            }
            return response.json();
        })
        .then(data => {
            resultsContainer.innerHTML = ""; // Clear previous suggestions

            if (data.suggestions.length > 0) {
                data.suggestions.forEach(suggestion => {
                    const item = document.createElement("div");
                    item.classList.add("p-2", "hover:bg-gray-100", "cursor-pointer");
                    item.textContent = suggestion;

                    // Clicking a suggestion fills the input and performs search
                    item.onclick = () => {
                        document.getElementById(inputId).value = suggestion;
                        resultsContainer.classList.add("hidden");
                        performSearch(inputId);
                    };

                    resultsContainer.appendChild(item);
                });

                resultsContainer.classList.remove("hidden"); // Show suggestions
            } else {
                resultsContainer.classList.add("hidden");
            }
        })
        .catch(error => console.error("Error fetching suggestions:", error));
}




// perform search when search button clicked
function performSearch(inputId) {
    const query = document.getElementById(inputId).value.trim();
    if (query) {
        window.location.href = `/search-results?query=${encodeURIComponent(query)}`;
    }
}

// hide search results when clicked outside
document.addEventListener("click", (event) => {
    ["search-results", "search-results-mobile"].forEach(resultsId => {
        const resultsContainer = document.getElementById(resultsId);
        if (resultsContainer && !resultsContainer.contains(event.target)) {
            resultsContainer.classList.add("hidden");
        }
    });
});






