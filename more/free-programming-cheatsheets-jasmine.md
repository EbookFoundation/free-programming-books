jasmine statements:

describe( label, function(){ ... })

group tests together

it( label, function(){ ... })

label individual test

expect( actual )

used to compare against expected values

beforeEach(function(){ ... })

run prior to each it in the describe

afterEach(function() { ... })

run after each it in the describe

xdescribe( label, function(){ ... })

skip section ( note the x )

xit( label, function(){ ... })

skip test ( note the x )

jasmine matchers 

to(Not)Be( null | true | false )
to(Not)Equal( value )
to(Not)Match( regex | string )
toBeDefined()
toBeUndefined()
toBeNull()
toBeTruthy()
toBeFalsy()
to(Not)Contain( string )
toBeLessThan( number )
toBeGreaterThan( number )
toBeNaN()
toBeCloseTo( number, precision )
toThrow()

jasmine doubles/spies

spyOn( obj, method_string )
obj.stubbed.calls
array
obj.stubbed.mostRecentCall
call object
obj.stubbed.calls[0].args
array
toHaveBeenCalled()
toHaveBeenCalledWith( array )
andCallThrough()
spy and delegate to real object
andReturn( value )
andCallFake(function() { ... })
jasmine.createSpy( id )
jasmine.createSpyObj( baseName, methods[] )
jasmine.any( constructor )
