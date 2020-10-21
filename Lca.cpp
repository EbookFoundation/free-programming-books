#include <bits/stdc++.h>
 
#define ll long long
#define ld long double
#define ull unsigned ll
#define ioi exit(0);
 
#define inf (int)1e9+7
 
#define F first
#define S second
 
#define pb push_back
#define ppb pop_back
 
#define lb(x) lower_bound(x)
#define ub(x) upper_bound(x)
 
#define sz(x) x.size()
 
#define all(x) x.begin(),x.end()
 
#define NFS ios_base :: sync_with_stdio(0), cin.tie(0), cout.tie(0);
 
const int N=2e3+7;
 
using namespace std;
 
vector<int> g[N];
int tin[N];
int timer;
bool used[N];
int tout[N];
int up[N][35];
vector<pair<int, int> > q;
// tin, tout - this is entry and exit timer  
bool is_parent(int x, int y){
    return tin[x] <= tin[y] && tout [x] >= tout[y]; //
}
void dfs(int v){
    used[v] = 1;
    tin[v] = ++timer;
 
    for(auto it:g[v]){
        if(!used[it]){
            up[it][0] = v;
            dfs(it);
        }
    }
 
    tout[v] = ++timer;
 
}
 
int lca(int x, int y){
 
    if(is_parent(x, y)) return x;
    if(is_parent(y, x)) return y;
 
    int pos = x;
 
    for(int i = 15; i >= 0; i--){
        if(up[pos][i] != 0 && is_parent(up[pos][i], y) == 0){
            pos = up[pos][i];
        }
    }
    return up[pos][0];
}
 
main () {
 
    NFS
 
    int tt;
    cin >> tt;
 
    for(int i = 1; i <= tt; i++){
        string s;
        cin >> s;
 
        int l, r;
        cin >> l >> r;
 
        if(s[0] == 'A'){
            g[l].pb(r);
            g[r].pb(l);
        }
        else{
            q.pb({l, r});
        }
    }
 
    dfs(1);
 
    for(int i = 1; i <= 15; i++){
        for(int j = 1; j <= 1000; j++){
            up[j][i] = up[up[j][i - 1]][i - 1];
        }
    }
 
    for(int i = 0; i < sz(q); i++){
        cout << lca(q[i].F, q[i].S) << endl;
    }
 
    ioi
}

// this problem you can find with this link https://codeforces.com/gym/100091
