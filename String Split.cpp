#include <bits/stdc++.h>
using namespace std;
int main() {
    string a="hi i am, krishna Sen";
    stringstream aa(a);
    string b="";
    vector<string> v;
    while(getline(aa,a,' ')){
        v.push_back(a);
    }
    for(auto i:v) cout<<i<<endl;
    return 0;
}