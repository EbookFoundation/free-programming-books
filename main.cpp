//memo

#include <bits/stdc++.h>
using namespace std;

// Function to find the maximum chocolates that can be collected recursively
int maxChocoUtil(int i, int j1, int j2, int n, int m, vector<vector<int>> &grid, vector<vector<vector<int>>> &dp) {
    // Check if the positions (j1, j2) are valid
    if (j1 < 0 || j1 >= m || j2 < 0 || j2 >= m)
        return -1e9; // A very large negative value to represent an invalid position

    // Base case: If we are at the last row, return the chocolate at the positions (j1, j2)
    if (i == n - 1) {
        if (j1 == j2)
            return grid[i][j1];
        else
            return grid[i][j1] + grid[i][j2];
    }

    // If the result for this state is already computed, return it
    if (dp[i][j1][j2] != -1)
        return dp[i][j1][j2];

    int maxi = INT_MIN;
    
    // Try all possible moves (up, left, right) for both positions (j1, j2)
    for (int di = -1; di <= 1; di++) {
        for (int dj = -1; dj <= 1; dj++) {
            int ans;
            
            if (j1 == j2)
                ans = grid[i][j1] + maxChocoUtil(i + 1, j1 + di, j2 + dj, n, m, grid, dp);
            else
                ans = grid[i][j1] + grid[i][j2] + maxChocoUtil(i + 1, j1 + di, j2 + dj, n, m, grid, dp);
            
            // Update the maximum result
            maxi = max(maxi, ans);
        }
    }
    
    // Store the maximum result for this state in dp
    return dp[i][j1][j2] = maxi;
}

// Function to find the maximum chocolates that can be collected
int maximumChocolates(int n, int m, vector<vector<int>> &grid) {
    // Create a 3D DP array to store computed results
    vector<vector<vector<int>>> dp(n, vector<vector<int>>(m, vector<int>(m, -1)));

    // Call the recursive utility function to find the maximum chocolates starting from the first row
    return maxChocoUtil(0, 0, m - 1, n, m, grid, dp);
}

int main() {
    // Define the grid as a 2D vector
    vector<vector<int>> matrix{
        {2, 3, 1, 2},
        {3, 4, 2, 2},
        {5, 6, 3, 5},
    };

    int n = matrix.size();
    int m = matrix[0].size();

    // Call the maximumChocolates function and print the result
    cout << maximumChocolates(n, m, matrix);

    return 0;
}


//tabulation

#include <bits/stdc++.h>
using namespace std;

// Function to find the maximum chocolates that can be collected
int maximumChocolates(int n, int m, vector<vector<int>> &grid) {
    // Create a 3D DP array to store computed results
    vector<vector<vector<int>>> dp(n, vector<vector<int>>(m, vector<int>(m, 0)));

    // Initialize the DP array for the last row
    for (int j1 = 0; j1 < m; j1++) {
        for (int j2 = 0; j2 < m; j2++) {
            if (j1 == j2)
                dp[n - 1][j1][j2] = grid[n - 1][j1];
            else
                dp[n - 1][j1][j2] = grid[n - 1][j1] + grid[n - 1][j2];
        }
    }

    // Outer nested loops for traversing the DP array from the second-to-last row up to the first row
    for (int i = n - 2; i >= 0; i--) {
        for (int j1 = 0; j1 < m; j1++) {
            for (int j2 = 0; j2 < m; j2++) {
                int maxi = INT_MIN;

                // Inner nested loops to try out 9 options (diagonal moves)
                for (int di = -1; di <= 1; di++) {
                    for (int dj = -1; dj <= 1; dj++) {
                        int ans;

                        if (j1 == j2)
                            ans = grid[i][j1];
                        else
                            ans = grid[i][j1] + grid[i][j2];

                        // Check if the move is valid (within the grid boundaries)
                        if ((j1 + di < 0 || j1 + di >= m) || (j2 + dj < 0 || j2 + dj >= m))
                            ans += -1e9; // A very large negative value to represent an invalid move
                        else
                            ans += dp[i + 1][j1 + di][j2 + dj]; // Include the DP result from the next row

                        maxi = max(ans, maxi); // Update the maximum result
                    }
                }
                dp[i][j1][j2] = maxi; // Store the maximum result for this state in the DP array
            }
        }
    }

    // The maximum chocolates that can be collected is stored at the top-left corner of the DP array
    return dp[0][0][m - 1];
}

int main() {
    // Define the grid as a 2D vector
    vector<vector<int>> matrix{
        {2, 3, 1, 2},
        {3, 4, 2, 2},
        {5, 6, 3, 5},
    };

    int n = matrix.size(); // Number of rows
    int m = matrix[0].size(); // Number of columns

    // Call the maximumChocolates function and print the result
    cout << maximumChocolates(n, m, matrix);

    return 0;
}

//space opt


#include <bits/stdc++.h>
using namespace std;

// Function to find the maximum chocolates that can be collected
int maximumChocolates(int n, int m, vector<vector<int>> &grid) {
    // Create two 2D vectors 'front' and 'cur' to store computed results
    vector<vector<int>> front(m, vector<int>(m, 0));
    vector<vector<int>> cur(m, vector<int>(m, 0));

    // Initialize 'front' for the last row
    for (int j1 = 0; j1 < m; j1++) {
        for (int j2 = 0; j2 < m; j2++) {
            if (j1 == j2)
                front[j1][j2] = grid[n - 1][j1];
            else
                front[j1][j2] = grid[n - 1][j1] + grid[n - 1][j2];
        }
    }

    // Outer nested loops for traversing the DP array from the second-to-last row up to the first row
    for (int i = n - 2; i >= 0; i--) {
        for (int j1 = 0; j1 < m; j1++) {
            for (int j2 = 0; j2 < m; j2++) {
                int maxi = INT_MIN;

                // Inner nested loops to try out 9 options (diagonal moves)
                for (int di = -1; di <= 1; di++) {
                    for (int dj = -1; dj <= 1; dj++) {
                        int ans;

                        if (j1 == j2)
                            ans = grid[i][j1];
                        else
                            ans = grid[i][j1] + grid[i][j2];

                        // Check if the move is valid (within the grid boundaries)
                        if ((j1 + di < 0 || j1 + di >= m) || (j2 + dj < 0 || j2 + dj >= m))
                            ans += -1e9; // A very large negative value to represent an invalid move
                        else
                            ans += front[j1 + di][j2 + dj]; // Include the value from the 'front' array

                        maxi = max(ans, maxi); // Update the maximum result
                    }
                }
                cur[j1][j2] = maxi; // Store the maximum result for this state in the 'cur' array
            }
        }
        front = cur; // Update 'front' with the values from 'cur' for the next iteration
    }

    // The maximum chocolates that can be collected is stored at the top-left corner of the 'front' array
    return front[0][m - 1];
}

int main() {
    // Define the grid as a 2D vector
    vector<vector<int>> matrix{
        {2, 3, 1, 2},
        {3, 4, 2, 2},
        {5, 6, 3, 5},
    };

    int n = matrix.size(); // Number of rows
    int m = matrix[0].size(); // Number of columns

    // Call the maximumChocolates function and print the result
    cout << maximumChocolates(n, m, matrix);

    return 0;
}

