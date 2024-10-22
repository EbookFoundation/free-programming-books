class Solution {
    public int findContentChildren(int[] g, int[] s) {
        
        Arrays.sort(g);
        Arrays.sort(s);

        int l = 0 , r = 0 ;
        int n = g.length ;
        int m = s.length ;

        while( l < n && r < m){
            if( g[l] <= s[r] ) l++ ;
            r++ ;
        }
        return l ;
    }
}
