from pyflowsheet import Flowsheet, UnitOperation, Distillation, Vessel, BlackBox, Pump, Stream, StreamFlag, Valve,HeatExchanger, Mixer, Splitter, Port, SvgContext
from pyflowsheet.internals import Tubes,RandomPacking
from pyflowsheet import VerticalLabelAlignment, HorizontalLabelAlignment
import os

# Create img directory if it doesn't exist
os.makedirs('img', exist_ok=True)

pfd= Flowsheet("V100-DS10","Complex Distillation", "Demo Flowsheet for testing externalized columns peripherals and routing")

Feed= StreamFlag("Feed", "Feed", position=(0,250))
HX1=HeatExchanger("Preheater","Pre-Heater", position=(160,250))
TWR1=Distillation("Tower","Distillation Tower", hasCondenser=False, hasReboiler=False,position=(300,120), size=(40,300), internals=[RandomPacking(start=0, end=0.4),RandomPacking(start=0.6, end=1.0)])
MX1= Mixer("MX1", "Mixer", position=(400,450))
SP1= Splitter("SP1", "Splitter", position=(460,450))
REB=Vessel("Reboiler","Falling Film Evaporator", position=(390,340), size=(40,80),capLength=20,internals=[Tubes(7)] )
REB.ports["Out2"] = Port("Out2", REB, (0, .25), (-1, 0), intent="out")
COND=Vessel("Condenser","Condenser", position=(390,40), size=(40,100), internals=[Tubes()])
COND.ports["Out2"] = Port("Out2", COND, (0, 0.15), (-1, 0), intent="out")


SP2= Splitter("SP2", "Reflux-Splitter", position=(500,130))
P1= StreamFlag("P1", "Product 1", position=(560,120))
P2= StreamFlag("P2", "Product 2", position=(0,400))
P3= StreamFlag("P3", "Product 3", position=(560,0))

#rotate units to resemble the actual plant layout

COND.rotate(105)

SP2.rotate(90)
P2.flip(axis="horizontal")
REB.flip(axis="vertical")

pfd.addUnits( [Feed,HX1,TWR1,MX1, SP1, REB,COND,SP2, P1,P2,P3] )

pfd.connect("S01", Feed["Out"], HX1["TIn"] ) 
pfd.connect("S02", HX1["TOut"], TWR1["Feed"] ) 
pfd.connect("S04", TWR1["LOut"], MX1["In1"] ) 
pfd.connect("S05", HX1["SOut"], P2["In"] ) 
pfd.connect("S06", MX1["Out"], SP1["In"] ) 
pfd.connect("S08", SP1["Out2"], REB["In"] ) 
pfd.connect("S09", REB["Out"], MX1["In2"] ) 
pfd.connect("S10", REB["Out2"], TWR1["VIn"] ) 
pfd.connect("S11", TWR1["VOut"], COND["In"] ) 
pfd.connect("S12", COND["Out"], SP2["In"] )
pfd.connect("S13", SP2["Out2"], P1["In"] ) 
pfd.connect("S14", SP2["Out3"], TWR1["RIn"] ) 
pfd.connect("S15", COND["Out2"], P3["In"] )
pfd.connect("S07", SP1["Out1"], HX1["SIn"] ) 

#If you do not like the automatic stream layout, you can manually define a sequence of relative steps (relative to last point). The first element is the difference in x direction, the second element is the difference in y. The route starts at the source connector.

pfd.streams["S07"].manualRouting=[(14,0),(0,30),(-240,0),(0,-260),(-70,0)] 
pfd.streams["S05"].labelOffset=(10,30)
pfd.streams["S07"].labelOffset=(25,10)
pfd.streams["S15"].labelOffset=(10,-10)
pfd.streams["S11"].labelOffset=(10,-10)

#Change the label positions to make them more readable
TWR1.setTextAnchor(HorizontalLabelAlignment.RightOuter,VerticalLabelAlignment.Center,(10,0) )
REB.setTextAnchor(HorizontalLabelAlignment.RightOuter,VerticalLabelAlignment.Center,(10,0) )

ctx= SvgContext("img/externalized_column_with_preheater.svg")
img = pfd.draw(ctx)
ctx.render(width=1280, height=640, scale=1, saveFile=True)
print("SVG file has been saved to img/externalized_column_with_preheater.svg")