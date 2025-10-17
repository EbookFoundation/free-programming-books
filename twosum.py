class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        # Create a hash map to store numbers and their indices
        num_map = {}
        
        # Iterate through the array
        for i, num in enumerate(nums):
            # Calculate the complement needed to reach the target
            complement = target - num
            
            # If the complement exists in the hash map, we found the pair
            if complement in num_map:
                return [num_map[complement], i]
            
            # Otherwise, add the current number and its index to the hash map
            num_map[num] = i
        
        # If no solution is found (though the problem states one always exists)
        return []
