import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue
from pathlib import Path
import math
import os

ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()  # Queue for thread-safe actions

# Event Handler Variables
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None

#Event Handler Class
class TaskEventHandler(adsk.core.CustomEventHandler):
    """
    Custom Event Handler for processing tasks from the queue
    This is used, because Fusion 360 API is not thread-safe
    """
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        global task_queue, ModelParameterSnapshot, design, ui
        try:
            app = adsk.core.Application.get()
            if not app:
                return
            ui = app.userInterface
            
            if app.activeProduct:
                design = adsk.fusion.Design.cast(app.activeProduct)
            
            if design:
                # Update parameter snapshot
                ModelParameterSnapshot = get_model_parameters(design)
                
                # Process task queue
                while not task_queue.empty():
                    try:
                        task = task_queue.get_nowait()
                        self.process_task(task)
                    except queue.Empty:
                        break
                    except Exception as e:
                        if ui:
                            print(f"Task error: {str(e)}")
                        continue
                        
        except Exception as e:
            pass
    
    def process_task(self, task):
        """Processes a single task"""
        global design, ui
        
        if task[0] == 'set_parameter':
            set_parameter(design, ui, task[1], task[2])
        elif task[0] == 'draw_box':
            
            draw_Box(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            
        elif task[0] == 'draw_witzenmann':
            draw_Witzenmann(design, ui, task[1],task[2])
        elif task[0] == 'export_stl':
            export_as_STL(design, ui, task[1])
        elif task[0] == 'capture_image':
            capture_image(app, ui, task[1])
        elif task[0] == 'fillet_edges':
            fillet_edges(design, ui, task[1])
        elif task[0] == 'export_step':

            export_as_STEP(design, ui, task[1])
        elif task[0] == 'draw_cylinder':
            draw_cylinder(design, ui, task[1], task[2], task[3], task[4], task[5],task[6])
        elif task[0] == 'shell_body':
            shell_existing_body(design, ui, task[1], task[2])
        elif task[0] == 'undo':
            undo(design, ui)
        elif task[0] == 'draw_lines':
            draw_lines(design, ui, task[1], task[2], task[3])
        elif task[0] == 'extrude_last_sketch':
            extrude_last_sketch(design, ui, task[1],task[2])
        elif task[0] == 'revolve_profile':
            # 'rootComp = design.rootComponent
            # sketches = rootComp.sketches
            # sketch = sketches.item(sketches.count - 1)  # Last sketch
            # axisLine = sketch.sketchCurves.sketchLines.item(0)  # First line as axis'
            revolve_profile(design, ui,  task[1])        
        elif task[0] == 'arc':
            arc(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'draw_one_line':
            draw_one_line(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'holes': #task format: ('holes', points, width, depth, through, faceindex)
            # task[3]=depth, task[4]=through, task[5]=faceindex
            holes(design, ui, task[1], task[2], task[3], task[4])
        elif task[0] == 'circle':
            draw_circle(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'extrude_thin':
            extrude_thin(design, ui, task[1],task[2])
        elif task[0] == 'select_body':
            select_body(design, ui, task[1])
        elif task[0] == 'select_sketch':
            select_sketch(design, ui, task[1])
        elif task[0] == 'spline':
            spline(design, ui, task[1], task[2])
        elif task[0] == 'sweep':
            sweep(design, ui)
        elif task[0] == 'cut_extrude':
            cut_extrude(design,ui,task[1])
        elif task[0] == 'circular_pattern':
            circular_pattern(design,ui,task[1],task[2],task[3])
        elif task[0] == 'offsetplane':
            offsetplane(design,ui,task[1],task[2])
        elif task[0] == 'loft':
            loft(design, ui, task[1])
        elif task[0] == 'ellipsis':
            draw_ellipis(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7],task[8],task[9],task[10])
        elif task[0] == 'draw_sphere':
            plane = task[5] if len(task) > 5 else "XY"
            create_sphere(design, ui, task[1], task[2], task[3], task[4], plane)
        elif task[0] == 'threaded':
            # task format: ('threaded', inside, sizes, body_idx, face_idx, radius)
            # task_queue.put(('threaded', inside, allsizes, body_index, face_index, radius))
            # task[0] is 'threaded'
            # task[1] is inside
            # task[2] is allsizes
            # task[3] is body_index
            # task[4] is face_index
            # task[5] is radius
            inside = task[1]
            sizes = task[2]
            body_idx = task[3] if len(task) > 3 else -1
            face_idx = task[4] if len(task) > 4 else -1
            radius = task[5] if len(task) > 5 else -1
            create_thread(design, ui, inside, sizes, body_idx, face_idx, radius)
        elif task[0] == 'delete_everything':
            delete(design, ui)
        elif task[0] == 'boolean_operation':
            op = task[1]
            target_idx = task[2] if len(task) > 2 else 0
            tool_idx = task[3] if len(task) > 3 else 1
            boolean_operation(design, ui, op, target_idx, tool_idx)
        elif task[0] == 'draw_2d_rectangle':
            draw_2d_rect(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'rectangular_pattern':
            rect_pattern(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7])
        elif task[0] == 'draw_text':
            draw_text(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10], task[11])
        elif task[0] == 'move_body':
            move_last_body(design,ui,task[1],task[2],task[3])
        elif task[0] == 'new_design':
            create_new_design(app, ui)
        elif task[0] == 'set_appearance':
            set_appearance(design, ui, task[1])
        elif task[0] == 'run_script':
            try:
                code = task[1]
                exec_globals = {
                    'adsk': adsk,
                    'app': adsk.core.Application.get(),
                    'ui': ui,
                    'design': design,
                    'root': (design.rootComponent if design else None)
                }
                exec(code, exec_globals)
            except Exception as e:
                if ui:
                    print(f'Script Error: {str(e)}')
        elif task[0] == 'add_snap_fit_joint':
            try:
                # task format: ('add_snap_fit_joint', f_idx, fx, fy, fz, m_idx, mx, my, mz, radius)
                f_idx, fx, fy, fz, m_idx, mx, my, mz, radius = task[1:]
                
                # Dimensions with robust tolerances
                entry_radius = radius + 0.02 # Hole slightly larger than nominal (5.4mm for r=0.25)
                cavity_radius = radius + 0.15 # Internal cavity wide enough for expansion
                shaft_radius = radius - 0.04 # 0.4mm clearance for the shaft
                head_radius = radius + 0.08  # 0.6mm total snap engagement vs entry hole
                
                # 1. Female Features (Lower body hole pointing UP)
                # Entry Hole
                draw_cylinder(design, ui, entry_radius, -0.35, fx, fy, fz + 0.05)
                boolean_operation(design, ui, "cut", target_idx=f_idx, tool_idx=-1)
                # Cavity
                draw_cylinder(design, ui, cavity_radius, -0.85, fx, fy, fz - 0.25)
                boolean_operation(design, ui, "cut", target_idx=f_idx, tool_idx=-1)
                
                # 2. Male Features (Upper body snap pointing DOWN)
                # Shaft
                draw_cylinder(design, ui, shaft_radius, -0.3, mx, my, mz + 0.05)
                boolean_operation(design, ui, "join", target_idx=m_idx, tool_idx=-1)
                # Mushroom Head
                draw_circle(design, ui, head_radius, mx, my, mz - 0.25)
                extrude_last_sketch(design, ui, -0.15, 45) 
                boolean_operation(design, ui, "join", target_idx=m_idx, tool_idx=-1)
                # Relief Slit
                slit_width = (radius * 2) * 0.4
                draw_Box(design, ui, 1.0, slit_width, -0.6, mx, my, mz)
                boolean_operation(design, ui, "cut", target_idx=m_idx, tool_idx=-1)
            except Exception as e:
                if ui: print(f"Error adding snap joint: {str(e)}\n{traceback.format_exc()}")
        


class TaskThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Alle 200ms Custom Event feuern für Task-Verarbeitung
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break



###Geometry Functions######

def draw_text(design, ui, text, thickness,
              x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane="XY", faceindex=-1):
    
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if faceindex != -1:
            bodies = rootComp.bRepBodies
            if bodies.count > 0:
                latest_body = bodies.item(bodies.count - 1)
                if faceindex < latest_body.faces.count:
                    face = latest_body.faces.item(faceindex)
                    sketch = sketches.add(face)
                else:
                    sketch = sketches.add(rootComp.xYConstructionPlane)
            else:
                sketch = sketches.add(rootComp.xYConstructionPlane)
        else:
            if plane == "XY":
                sketch = sketches.add(rootComp.xYConstructionPlane)
            elif plane == "XZ":
                sketch = sketches.add(rootComp.xZConstructionPlane)
            elif plane == "YZ":
                sketch = sketches.add(rootComp.yZConstructionPlane)
            else:
                sketch = sketches.add(rootComp.xYConstructionPlane)

        # In Fusion 360, when creating sketch entities, the points should be on the sketch plane.
        # We use modelToSketchSpace to ensure the 3D world points are correctly projected.
        point_1_world = adsk.core.Point3D.create(x_1, y_1, z_1)
        point_2_world = adsk.core.Point3D.create(x_2, y_2, z_2)
        
        point_1 = sketch.modelToSketchSpace(point_1_world)
        point_2 = sketch.modelToSketchSpace(point_2_world)

        texts = sketch.sketchTexts
        input = texts.createInput2(f"{text}", thickness)
        input.setAsMultiLine(point_1,
                             point_2,
                             adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                             adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        sketchtext = texts.add(input)
        extrudes = rootComp.features.extrudeFeatures
        
        # Use Join for embossing if possible, otherwise NewBody
        operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        extInput = extrudes.createInput(sketchtext, operation)
        distance = adsk.core.ValueInput.createByReal(extrusion_value)
        extInput.setDistanceExtent(False, distance)
        extInput.isSolid = True
        
        # Create the extrusion
        try:
            ext = extrudes.add(extInput)
        except:
            # Fallback to NewBody if Join fails (e.g. if text is not touching body)
            extInput = extrudes.createInput(sketchtext, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extInput.setDistanceExtent(False, distance)
            extInput.isSolid = True
            ext = extrudes.add(extInput)

    except:
        if ui:
            print('Failed draw_text:\n{}'.format(traceback.format_exc()))
def create_sphere(design, ui, radius, x, y, z, plane="XY"):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            offset_val = y
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            offset_val = x
        else:
            basePlane = rootComp.xYConstructionPlane
            offset_val = z

        if offset_val != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(offset_val)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
            
        # Draw a circle.
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x,y,z), radius)
        # Draw a line to use as the axis of revolution.
        lines = sketch.sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(
            adsk.core.Point3D.create(x - radius, y, z),
            adsk.core.Point3D.create(x + radius, y, z)
        )

        # Get the profile defined by half of the circle.
        profile = sketch.profiles.item(0)
        # Create an revolution input for a revolution while specifying the profile and that a new component is to be created
        revolves = component.features.revolveFeatures
        revInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # Define that the extent is an angle of 2*pi to get a sphere
        angle = adsk.core.ValueInput.createByReal(2*math.pi)
        revInput.setAngleExtent(False, angle)
        # Create the extrusion.
        ext = revolves.add(revInput)
        
        
    except:
        if ui :
            print('Failed create_sphere:\n{}'.format(traceback.format_exc()))





def draw_Box(design, ui, height, width, depth,x,y,z, plane=None):
    """
    Draws Box with given dimensions height, width, depth at position (x,y,z)
    z creates an offset construction plane
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        # Choose base plane based on parameter
        if plane == 'XZ':
            basePlane = rootComp.xZConstructionPlane
        elif plane == 'YZ':
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane
        
        # Create offset plane at z if z != 0
        if z != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        
        lines = sketch.sketchCurves.sketchLines
        # addCenterPointRectangle: (center, corner-relative-to-center)
        lines.addCenterPointRectangle(
            adsk.core.Point3D.create(x, y, 0),
            adsk.core.Point3D.create(x + width/2, y + height/2, 0)
        )
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
    except:
        if ui:
            print('Failed draw_Box:\n{}'.format(traceback.format_exc()))

def draw_ellipis(design,ui,x_center,y_center,z_center,
                 x_major, y_major,z_major,x_through,y_through,z_through,plane ="XY"):
    """
    Draws an ellipse on the specified plane using three points.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        # Always define the points and create the ellipse
        # Ensure all arguments are floats (Fusion API is strict)
        centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
        majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
        throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
        sketchEllipse = sketch.sketchCurves.sketchEllipses
        ellipse = sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)
    except:
        if ui:
            print('Failed to draw ellipsis:\n{}'.format(traceback.format_exc()))

def draw_2d_rect(design, ui, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes

    if plane == "XZ":
        baseplane = rootComp.xZConstructionPlane
        if y_1 and y_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(y_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    elif plane == "YZ":
        baseplane = rootComp.yZConstructionPlane
        if x_1 and x_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(x_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    else:
        baseplane = rootComp.xYConstructionPlane
        if z_1 and z_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)

    rectangles = sketch.sketchCurves.sketchLines
    point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
    points_2 = adsk.core.Point3D.create(x_2, y_2, z_2)
    rectangles.addTwoPointRectangle(point_1, points_2)



def draw_circle(design, ui, radius, x, y, z, plane="XY"):
    
    """
    Draws a circle with given radius at position (x,y,z) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    For XY plane: circle at (x,y) with z offset
    For XZ plane: circle at (x,z) with y offset  
    For YZ plane: circle at (y,z) with x offset
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        # Determine which plane and coordinates to use
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            # For XZ plane: x and z are in-plane, y is the offset
            if y != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(y)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, z, 0)
            
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            # For YZ plane: y and z are in-plane, x is the offset
            if x != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(y, z, 0)
            
        else:  # XY plane (default)
            basePlane = rootComp.xYConstructionPlane
            # For XY plane: x and y are in-plane, z is the offset
            if z != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(z)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, y, 0)
    
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(centerPoint, radius)
    except:
        if ui:
            print('Failed draw_circle:\n{}'.format(traceback.format_exc()))




def draw_sphere(design, ui, radius, x, y, z):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.add(rootComp.xYConstructionPlane)
#USELESS  


def draw_Witzenmann(design, ui,scaling,z):
    """
    Draws Witzenmannlogo 
    can be scaled with scaling factor to make it bigger or smaller
    The z Position can be adjusted with z parameter
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283*scaling,10.475*scaling,z),(8.283*scaling,6.471*scaling,z),(-0.126*scaling,6.471*scaling,z),(8.283*scaling,2.691*scaling,z),
            (8.283*scaling,-1.235*scaling,z),(-0.496*scaling,-1.246*scaling,z),(8.283*scaling,-5.715*scaling,z),(8.283*scaling,-9.996*scaling,z),
            (-8.862*scaling,-1.247*scaling,z),(-8.859*scaling,2.69*scaling,z),(-0.639*scaling,2.69*scaling,z),(-8.859*scaling,6.409*scaling,z),
            (-8.859*scaling,10.459*scaling,z)
        ]
        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1],points1[i][2])
            end   = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1],points1[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end) # Draw connection line
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0],points1[-1][1],points1[-1][2]),
            adsk.core.Point3D.create(points1[0][0],points1[0][1],points1[0][2])
        )

        points2 = [(-3.391*scaling,-5.989*scaling,z),(5.062*scaling,-10.141*scaling,z),(-8.859*scaling,-10.141*scaling,z),(-8.859*scaling,-5.989*scaling,z)]
        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1],points2[i][2])
            end   = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1],points2[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1],points2[-1][2]),
            adsk.core.Point3D.create(points2[0][0], points2[0][1],points2[0][2])
        )

        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0*scaling)
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False,distance)
            extrudes.add(extrudeInput)

    except:
        if ui:
            print('Failed draw_Witzenmann:\n{}'.format(traceback.format_exc()))
def create_new_design(app, ui):
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        print("Created a new Fusion 360 design document.")
    except:
        if ui:
            print('Failed create_new_design:\n{}'.format(traceback.format_exc()))

##############################################################################################
###2D Geometry Functions######


def move_last_body(design,ui,x,y,z):
    
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        sketches = rootComp.sketches
        moveFeats = features.moveFeatures
        body = rootComp.bRepBodies
        bodies = adsk.core.ObjectCollection.create()
        
        if body.count > 0:
                latest_body = body.item(body.count - 1)
                bodies.add(latest_body)
        else:
            print("No bodies found.")
            return

        vector = adsk.core.Vector3D.create(x,y,z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        moveFeatureInput = moveFeats.createInput2(bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)
    except:
        if ui:
            print('Failed to move the body:\n{}'.format(traceback.format_exc()))


def set_appearance(design, ui, appearance_name):
    """
    Applies an appearance to the latest body in Fusion 360
    """
    try:
        app = adsk.core.Application.get()
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if bodies.count == 0:
            if ui:
                print("No bodies found to color.")
            return

        latest_body = bodies.item(bodies.count - 1)
        
        # Look for the appearance in the design first
        appearance = design.appearances.itemByName(appearance_name)
        
        if not appearance:
            # Look in the Fusion 360 Appearance Library
            lib = app.materialLibraries.itemByName('Fusion 360 Appearance Library')
            if lib:
                try:
                    lib_appearance = lib.appearances.itemByName(appearance_name)
                    if not lib_appearance:
                        # Simple search for partial matches if exact match fails
                        for a in lib.appearances:
                            if appearance_name.lower() in a.name.lower():
                                lib_appearance = a
                                break
                    
                    if lib_appearance:
                        appearance = design.appearances.addByCopy(lib_appearance, appearance_name)
                except:
                    pass
            
            if not appearance:
                if ui:
                    print(f"Appearance '{appearance_name}' was not found.")
                return

        latest_body.appearance = appearance
        
    except Exception as e:
        if ui:
            print(f"Set Appearance failed:\n{traceback.format_exc()}")


def offsetplane(design,ui,offset,plane ="XY"):

    """,
    Creates a new offset sketch which can be selected
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        offset = adsk.core.ValueInput.createByReal(offset)
        ctorPlanes = rootComp.constructionPlanes
        ctorPlaneInput1 = ctorPlanes.createInput()
        
        if plane == "XY":         
            ctorPlaneInput1.setByOffset(rootComp.xYConstructionPlane, offset)
        elif plane == "XZ":
            ctorPlaneInput1.setByOffset(rootComp.xZConstructionPlane, offset)
        elif plane == "YZ":
            ctorPlaneInput1.setByOffset(rootComp.yZConstructionPlane, offset)
        ctorPlanes.add(ctorPlaneInput1)
    except:
        if ui:
            print('Failed offsetplane:\n{}'.format(traceback.format_exc()))



def create_thread(design, ui, inside, sizes, body_idx=-1, face_idx=-1, radius=-1):
    """
    params:
    inside: boolean information if the face is inside or outside
    sizes : index of the size in the allsizes list
    body_idx: Optional: Index of the body to select (programmatic selection)
    face_idx: Optional: Index of the face on the body (programmatic selection)
    radius: Optional: Radius of the cylindrical face to select (programmatic selection)
    """
    try:
        rootComp = design.rootComponent
        threadFeatures = rootComp.features.threadFeatures
        
        faces = adsk.core.ObjectCollection.create()
        
        if body_idx != -1:
            if body_idx >= rootComp.bRepBodies.count:
                if ui: print(f"Body index {body_idx} out of range. Total bodies: {rootComp.bRepBodies.count}")
                return
            body = rootComp.bRepBodies.item(body_idx)
            
            target_face = None
            if face_idx != -1:
                if face_idx < body.faces.count:
                    target_face = body.faces.item(face_idx)
            elif radius != -1:
                # Find cylindrical face with matching radius
                for face in body.faces:
                    try:
                        if face.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
                            # logging radius might be useful
                            if abs(face.geometry.radius - radius) < 0.001:
                                target_face = face
                                break
                    except:
                        continue
            
            if target_face:
                faces.add(target_face)
            else:
                if ui: print(f"Could not find matching face on body {body_idx}. Radius: {radius}, FaceIndex: {face_idx}")
                return
        else:
            if ui:
                print(f"DEBUG: body_idx is {body_idx}. Auto selection failed.")
            return

        # Get the thread infos
        threadDataQuery = threadFeatures.threadDataQuery
        threadTypes = threadDataQuery.allThreadTypes
        
        # Robust search for a thread type that supports the requested size index
        threadType = None
        threadSize = None
        
        debug_info = f"Requested size index: {sizes}. Available types: {len(threadTypes)}\n"
        
        for i in range(len(threadTypes)):
            tType = threadTypes[i]
            try:
                available_sizes = threadDataQuery.allSizes(tType)
                if sizes < len(available_sizes):
                    tSize = available_sizes[sizes]
                    # Verify designations exist for this size
                    allDesignations = threadDataQuery.allDesignations(tType, tSize)
                    if len(allDesignations) > 0:
                        threadType = tType
                        threadSize = tSize
                        break
                else:
                    debug_info += f"Type {tType}: only {len(available_sizes)} sizes.\n"
            except:
                continue
        
        if not threadType:
            if ui: print(f"Could not find a thread type for size index {sizes}.\n{debug_info}")
            return

        allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
        threadDesignation = allDesignations[0]
        
        allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
        threadClass = allClasses[0]
        
        # create the threadInfo according to the query result
        threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)
        
        threadInput = threadFeatures.createInput(faces, threadInfo)
        threadInput.isFullLength = True
        
        # create the final thread
        threadFeatures.add(threadInput)

    except: 
        if ui:
            print('Failed create_thread:\n{}'.format(traceback.format_exc()))







def spline(design, ui, points, plane="XY"):
    """
    Draws a spline through the given points on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        splinePoints = adsk.core.ObjectCollection.create()
        for point in points:
            splinePoints.add(adsk.core.Point3D.create(point[0], point[1], point[2]))
        
        sketch.sketchCurves.sketchFittedSplines.add(splinePoints)
    except:
        if ui:
            print('Failed draw_spline:\n{}'.format(traceback.format_exc()))





def arc(design,ui,point1,point2,points3,plane = "XY",connect = False):
    """
    This creates arc between two points on the specified plane
    """
    try:
        rootComp = design.rootComponent #Get the root component
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane 
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            xyPlane = rootComp.xYConstructionPlane 

            sketch = sketches.add(xyPlane)
        start  = adsk.core.Point3D.create(point1[0],point1[1],point1[2])
        alongpoint    = adsk.core.Point3D.create(point2[0],point2[1],point2[2])
        endpoint =adsk.core.Point3D.create(points3[0],points3[1],points3[2])
        arcs = sketch.sketchCurves.sketchArcs
        arc = arcs.addByThreePoints(start, alongpoint, endpoint)
        if connect:
            startconnect = adsk.core.Point3D.create(start.x, start.y, start.z)
            endconnect = adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(startconnect, endconnect)
            connect = False
        else:
            lines = sketch.sketchCurves.sketchLines

    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))


def draw_lines(design, ui, points, Plane="XY", faceindex=-1):
    """
    User input: points = [[x1,y1,z1], [x2,y2,z2], ...]
    Plane: "XY", "XZ", "YZ"
    Draws lines between the given points on the specified plane or face
    Connects the last point to the first point to close the shape
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if faceindex != -1:
            bodies = rootComp.bRepBodies
            if bodies.count > 0:
                latest_body = bodies.item(bodies.count - 1)
                if faceindex < latest_body.faces.count:
                    face = latest_body.faces.item(faceindex)
                    sketch = sketches.add(face)
                else:
                    sketch = sketches.add(rootComp.xYConstructionPlane)
            else:
                sketch = sketches.add(rootComp.xYConstructionPlane)
        else:
            if Plane == "XY":
                sketch = sketches.add(rootComp.xYConstructionPlane)
            elif Plane == "XZ":
                sketch = sketches.add(rootComp.xZConstructionPlane)
            elif Plane == "YZ":
                sketch = sketches.add(rootComp.yZConstructionPlane)
            else:
                sketch = sketches.add(rootComp.xYConstructionPlane)

        sketch_lines = sketch.sketchCurves.sketchLines
        
        # Project all points to sketch space
        sketch_points = []
        for p in points:
            # Ensure point has 3 coordinates
            pz = p[2] if len(p) > 2 else 0
            world_p = adsk.core.Point3D.create(float(p[0]), float(p[1]), float(pz))
            sketch_points.append(sketch.modelToSketchSpace(world_p))

        # Draw lines
        for i in range(len(sketch_points) - 1):
            sketch_lines.addByTwoPoints(sketch_points[i], sketch_points[i+1])
        
        # Close the loop
        if len(sketch_points) > 2:
            sketch_lines.addByTwoPoints(sketch_points[-1], sketch_points[0])

    except:
        if ui:
            print('Failed draw_lines:\n{}'.format(traceback.format_exc()))

def draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane="XY"):
    """
    Draws a single line between two points (x1, y1, z1) and (x2, y2, z2) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    This function does not add a new sketch it is designed to be used after arc 
    This is how we can make half circles and extrude them

    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        
        start = adsk.core.Point3D.create(x1, y1, 0)
        end = adsk.core.Point3D.create(x2, y2, 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))



#################################################################################



###3D Geometry Functions######
def loft(design, ui, sketchcount):
    """
    Creates a loft between the last 'sketchcount' sketches
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        loftFeatures = rootComp.features.loftFeatures
        
        loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        loftSectionsObj = loftInput.loftSections
        
        # Add profiles from the last 'sketchcount' sketches
        for i in range(sketchcount):
            sketch = sketches.item(sketches.count - 1 - i)
            profile = sketch.profiles.item(0)
            loftSectionsObj.add(profile)
        
        loftInput.isSolid = True
        loftInput.isClosed = False
        loftInput.isTangentEdgesMerged = True
        
        # Create loft feature
        loftFeatures.add(loftInput)
        
    except:
        if ui:
            print('Failed loft:\n{}'.format(traceback.format_exc()))



def boolean_operation(design,ui,op,target_idx=0,tool_idx=1):
    """
    This function performs boolean operations (cut, intersect, join)
    It uses target_idx and tool_idx to identify which bodies to use.
    If tool_idx is -1, it defaults to the last body.
    """
    try:
        app = adsk.core.Application.get()
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        ui  = app.userInterface

        # Get the root component of the active design.
        rootComp = design.rootComponent
        features = rootComp.features
        bodies = rootComp.bRepBodies
        
        if bodies.count <= target_idx:
            if ui: print(f"Target body index {target_idx} is out of bounds.")
            return
            
        if tool_idx == -1:
            tool_idx = bodies.count - 1
            
        if bodies.count <= tool_idx:
            if ui: print(f"Tool body index {tool_idx} is out of bounds.")
            return

        targetBody = bodies.item(target_idx)
        toolBody = bodies.item(tool_idx)

        
        combineFeatures = rootComp.features.combineFeatures
        tools = adsk.core.ObjectCollection.create()
        tools.add(toolBody)
        input: adsk.fusion.CombineFeatureInput = combineFeatures.createInput(targetBody, tools)
        input.isNewComponent = False
        input.isKeepToolBodies = False
        if op == "cut":
            input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif op == "intersect":
            input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        elif op == "join":
            input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            
        combineFeature = combineFeatures.add(input)
    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))






def sweep(design,ui):
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sweeps = rootComp.features.sweepFeatures

        profsketch = sketches.item(sketches.count - 2)  # Last sketch
        prof = profsketch.profiles.item(0) # Last profile in the sketch, i.e., the circle
        pathsketch = sketches.item(sketches.count - 1) # take the last sketch as path
        # collect all sketch curves in an ObjectCollection
        pathCurves = adsk.core.ObjectCollection.create()
        for i in range(pathsketch.sketchCurves.count):
            pathCurves.add(pathsketch.sketchCurves.item(i))

    
        path = adsk.fusion.Path.create(pathCurves, 0) # connec
        sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweeps.add(sweepInput)


def extrude_last_sketch(design, ui, value,taperangle):
    """
    Just extrudes the last sketch by the given value
    """
    try:
        rootComp = design.rootComponent 
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Last sketch
        prof = sketch.profiles.item(0)  # First profile in the sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)
        
        if taperangle != 0:
            taperValue = adsk.core.ValueInput.createByString(f'{taperangle} deg')
     
            extent_distance = adsk.fusion.DistanceExtentDefinition.create(distance)
            extrudeInput.setOneSideExtent(extent_distance, adsk.fusion.ExtentDirections.PositiveExtentDirection, taperValue)
        else:
            extrudeInput.setDistanceExtent(False, distance)
        
        extrudes.add(extrudeInput)
    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))

def shell_existing_body(design, ui, thickness=0.5, faceindex=0):
    """
    Shells the body on a specified face index with given thickness
    """
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        body = rootComp.bRepBodies.item(0)

        entities = adsk.core.ObjectCollection.create()
        entities.add(body.faces.item(faceindex))

        shellFeats = features.shellFeatures
        isTangentChain = False
        shellInput = shellFeats.createInput(entities, isTangentChain)

        thicknessVal = adsk.core.ValueInput.createByReal(thickness)
        shellInput.insideThickness = thicknessVal

        shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType

        # Execute
        shellFeats.add(shellInput)

    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))


def fillet_edges(design, ui, radius=0.3):
    try:
        rootComp = design.rootComponent

        bodies = rootComp.bRepBodies

        edgeCollection = adsk.core.ObjectCollection.create()
        for body_idx in range(bodies.count):
            body = bodies.item(body_idx)
            for edge_idx in range(body.edges.count):
                edge = body.edges.item(edge_idx)
                edgeCollection.add(edge)

        fillets = rootComp.features.filletFeatures
        radiusInput = adsk.core.ValueInput.createByReal(radius)
        filletInput = fillets.createInput()
        filletInput.isRollingBallCorner = True
        edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, True)
        edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
        fillets.add(filletInput)

    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))
def revolve_profile(design, ui,  angle=360):
    """
    Revolves the selected profile
    around the given axisLine by the specified angle (default is 360 degrees).
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if sketches.count == 0:
            print("No sketches found for revolve.")
            return
            
        sketch = sketches.item(sketches.count - 1)
        if sketch.profiles.count == 0:
            print("No profiles found in the last sketch.")
            return
        profile = sketch.profiles.item(0)
        
        if sketch.sketchCurves.sketchLines.count == 0:
            print("No sketch lines found for axis.")
            return
        axis = sketch.sketchCurves.sketchLines.item(0)
        
        operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        revolveFeatures = rootComp.features.revolveFeatures
        input = revolveFeatures.createInput(profile, axis, operation)
        input.setAngleExtent(False, adsk.core.ValueInput.createByString(str(angle) + ' deg'))
        revolveFeature = revolveFeatures.add(input)

    except:
        if ui:
            print('Failed revolve_profile:\n{}'.format(traceback.format_exc()))

##############################################################################################

###Selection Functions######
def rect_pattern(design,ui,axis_one ,axis_two ,quantity_one,quantity_two,distance_one,distance_two,plane="XY"):
    """
    Creates a rectangular pattern of the last body along the specified axis and plane
    There are two quantity parameters for two directions
    There are also two distance parameters for the spacing in two directions
    params:
    axis: "X", "Y", or "Z" axis for the pattern direction
    quantity_one: Number of instances in the first direction
    quantity_two: Number of instances in the second direction
    distance_one: Spacing between instances in the first direction
    distance_two: Spacing between instances in the second direction
    plane: Construction plane for the pattern ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        rectFeats = rootComp.features.rectangularPatternFeatures



        quantity_one = adsk.core.ValueInput.createByString(f"{quantity_one}")
        quantity_two = adsk.core.ValueInput.createByString(f"{quantity_two}")
        distance_one = adsk.core.ValueInput.createByString(f"{distance_one}")
        distance_two = adsk.core.ValueInput.createByString(f"{distance_two}")

        bodies = rootComp.bRepBodies
        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            print("No bodies found.")
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        baseaxis_one = None    
        if axis_one == "Y":
            baseaxis_one = rootComp.yConstructionAxis 
        elif axis_one == "X":
            baseaxis_one = rootComp.xConstructionAxis
        elif axis_one == "Z":
            baseaxis_one = rootComp.zConstructionAxis


        baseaxis_two = None    
        if axis_two == "Y":
            baseaxis_two = rootComp.yConstructionAxis  
        elif axis_two == "X":
            baseaxis_two = rootComp.xConstructionAxis
        elif axis_two == "Z":
            baseaxis_two = rootComp.zConstructionAxis

 

        rectangularPatternInput = rectFeats.createInput(inputEntites,baseaxis_one, quantity_one, distance_one, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        #second direction
        rectangularPatternInput.setDirectionTwo(baseaxis_two,quantity_two, distance_two)
        rectangularFeature = rectFeats.add(rectangularPatternInput)
    except:
        if ui:
            print('Failed to execute rectangular pattern:\n{}'.format(traceback.format_exc()))
        
        

def circular_pattern(design, ui, quantity, axis, plane):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            print("Keine Bodies gefunden.")
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)    
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        if axis == "Y":
            yAxis = rootComp.yConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, yAxis)
        elif axis == "X":
            xAxis = rootComp.xConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, xAxis)
        elif axis == "Z":
            zAxis = rootComp.zConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, zAxis)

        circularFeatInput.quantity = adsk.core.ValueInput.createByReal((quantity))
        circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        circularFeatInput.isSymmetric = False
        circularFeats.add(circularFeatInput)
        
        

    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))




def undo(design, ui):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        cmd = ui.commandDefinitions.itemById('UndoCommand')
        cmd.execute()

    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))


def delete(design,ui):
    """
    Remove every body and sketch from the design so nothing is left
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies
        removeFeat = rootComp.features.removeFeatures

        # Delete from back to front
        for i in range(bodies.count - 1, -1, -1): # starts at bodies.count - 1 and goes in steps of -1 to 0 
            body = bodies.item(i)
            removeFeat.add(body)

        
    except:
        if ui:
            print('Failed to delete:\n{}'.format(traceback.format_exc()))



def export_as_STEP(design, ui,Name):
    try:
        
        exportMgr = design.exportManager
              
        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.expanduser("~"), 'Desktop') 
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True) 
        
        stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path+ f'/{Name}.step')  # Save as Fusion.step in the export directory
       # stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path)       
        
        
        res = exportMgr.execute(stepOptions)
        if res:
            print(f"Exported STEP to: {Export_dir_path}")
        else:
            print("STEP export failed")
    except:
        if ui:
            print('Failed export_as_STEP:\n{}'.format(traceback.format_exc()))

def cut_extrude(design,ui,depth):
    try:
        rootComp = design.rootComponent 
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof,adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extrudeInput.setDistanceExtent(False, distance)
        extrudes.add(extrudeInput)
    except:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))


def extrude_thin(design, ui, thickness,distance):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    #print('Select a face for the extrusion.')
    #selectedFace = ui.selectEntity('Select a face for the extrusion.', 'Profiles').entity
    selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
    exts = rootComp.features.extrudeFeatures
    extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                            adsk.core.ValueInput.createByReal(thickness))

    distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance))
    extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

    ext = exts.add(extInput)


def draw_cylinder(design, ui, radius, height, x,y,z,plane = "XY"):
    """
    Draws a cylinder with given radius and height at position (x,y,z)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            offset_val = y
            cx, cy = x, z
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            offset_val = x
            cx, cy = y, z
        else:
            basePlane = rootComp.xYConstructionPlane
            offset_val = z
            cx, cy = x, y

        if offset_val != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(offset_val)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)

        center = adsk.core.Point3D.create(x, y, z)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(height)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)

    except:
        if ui:
            print('Failed draw_cylinder:\n{}'.format(traceback.format_exc()))



def capture_image(app, ui, filepath):
    try:
        app.activeViewport.saveAsImageFile(filepath, 1024, 1024)
        print(f"Captured screenshot to: {filepath}")
    except:
        if ui:
            print('Failed to capture image:\n{}'.format(traceback.format_exc()))

def export_as_STL(design, ui, Name):
    """
    Exports the entire root component as a single STL file.
    """
    try:
        rootComp = design.rootComponent
        exportMgr = design.exportManager

        if os.path.isabs(Name):
            full_path = Name
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
        else:
            directory_name = "Fusion_Exports"
            FilePath = os.path.join(os.path.expanduser("~"), 'Desktop') 
            Export_dir_path = os.path.join(FilePath, directory_name)
            os.makedirs(Export_dir_path, exist_ok=True) 
            full_path = os.path.join(Export_dir_path, f"{Name}.stl" if not Name.endswith('.stl') else Name)

        # Create STL export options for the root component
        stlExportOptions = exportMgr.createSTLExportOptions(rootComp, full_path)
        stlExportOptions.sendToPrintUtility = False
        
        res = exportMgr.execute(stlExportOptions)
        if res:
            print(f"Exported single STL to: {full_path}")
        else:
            print("STL export failed")

    except:
        if ui:
            print('Failed export_as_STL:\n{}'.format(traceback.format_exc()))

def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters
    for param in design.allParameters:
        if all(user_params.item(i) != param for i in range(user_params.count)):
            try:
                wert = str(param.value)
            except Exception:
                wert = ""
            model_params.append({
                "Name": str(param.name),
                "Value": wert,
                "Unit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            })
    return model_params

def set_parameter(design, ui, name, value):
    try:
        param = design.allParameters.itemByName(name)
        param.expression = value
    except:
        if ui:
            print('Failed set_parameter:\n{}'.format(traceback.format_exc()))

def holes(design, ui, points, width=1.0,distance = 1.0,faceindex=0):
    """
    Create one or more holes on a selected face.
    """
   
    try:
        rootComp = design.rootComponent
        holes = rootComp.features.holeFeatures
        sketches = rootComp.sketches
        
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            print("Keine Bodies gefunden.")
            return
        entities = adsk.core.ObjectCollection.create()
        entities.add(latest_body.faces.item(faceindex))
        sk = sketches.add(latest_body.faces.item(faceindex))# create sketch on faceindex face

        tipangle = 90.0
        for i in range(len(points)):
            holePoint = sk.sketchPoints.add(adsk.core.Point3D.create(points[i][0], points[i][1], 0))
            tipangle = adsk.core.ValueInput.createByString('180 deg')
            holedistance = adsk.core.ValueInput.createByReal(distance)
        
            holeDiam = adsk.core.ValueInput.createByReal(width)
            holeInput = holes.createSimpleInput(holeDiam)
            holeInput.tipAngle = tipangle
            holeInput.setPositionBySketchPoint(holePoint)
            holeInput.setDistanceExtent(holedistance)

        # Add the hole
            holes.add(holeInput)
    except Exception:
        if ui:
            print('Failed:\n{}'.format(traceback.format_exc()))



def select_body(design,ui,Bodyname):
    try: 
        rootComp = design.rootComponent 
        target_body = rootComp.bRepBodies.itemByName(Bodyname)
        if target_body is None:
            print(f"Body with the name:  '{Bodyname}' could not be found.")

        return target_body

    except : 
        if ui :
            print('Failed:\n{}'.format(traceback.format_exc()))

def select_sketch(design,ui,Sketchname):
    try: 
        rootComp = design.rootComponent 
        target_sketch = rootComp.sketches.itemByName(Sketchname)
        if target_sketch is None:
            print(f"Sketch with the name:  '{Sketchname}' could not be found.")

        return target_sketch

    except : 
        if ui :
            print('Failed:\n{}'.format(traceback.format_exc()))


# HTTP Server######
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ModelParameterSnapshot
        try:
            if self.path == '/count_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": len(ModelParameterSnapshot)}).encode('utf-8'))
            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))
           
            else:
                self.send_error(404,'Not Found')
        except Exception as e:
            self.send_error(500,str(e))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length',0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data) if post_data else {}
            path = self.path

            # Put all actions into the queue
            if path.startswith('/set_parameter'):
                name = data.get('name')
                value = data.get('value')
                if name and value:
                    task_queue.put(('set_parameter', name, value))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Parameter {name} is being set"}).encode('utf-8'))

            elif path == '/undo':
                task_queue.put(('undo',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Undo is being executed"}).encode('utf-8'))

            elif path == '/Box':
                height = float(data.get('height',5))
                width = float(data.get('width',5))
                depth = float(data.get('depth',5))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                Plane = data.get('plane',None)  # 'XY', 'XZ', 'YZ' or None

                task_queue.put(('draw_box', height, width, depth,x,y,z, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Box is being created"}).encode('utf-8'))

            elif path == '/Witzenmann':
                scale = data.get('scale',1.0)
                z = float(data.get('z',0))
                task_queue.put(('draw_witzenmann', scale,z))

                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Witzenmann logo is being created"}).encode('utf-8'))

            elif path == '/new_design':
                task_queue.put(('new_design',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Created new design"}).encode('utf-8'))
                
            elif path == '/capture_image':
                name = str(data.get('Name','Test.png'))
                task_queue.put(('capture_image', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": f"Captured image to {name}"}).encode('utf-8'))
                
            elif path == '/Export_STL':
                name = str(data.get('Name','Test.stl'))
                task_queue.put(('export_stl', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STL Export started"}).encode('utf-8'))


            elif path == '/Export_STEP':
                name = str(data.get('name','Test.step'))
                task_queue.put(('export_step',name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STEP Export started"}).encode('utf-8'))


            elif path == '/fillet_edges':
                radius = float(data.get('radius',0.3)) #0.3 as default
                task_queue.put(('fillet_edges',radius))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Fillet edges started"}).encode('utf-8'))

            elif path == '/draw_cylinder':
                radius = float(data.get('radius'))
                height = float(data.get('height'))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_cylinder', radius, height, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cylinder is being created"}).encode('utf-8'))
            

            elif path == '/shell_body':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                faceindex = int(data.get('faceindex',0))
                task_queue.put(('shell_body', thickness, faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Shell body is being created"}).encode('utf-8'))

            elif path == '/draw_lines':
                points = data.get('points', [])
                Plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                faceindex = int(data.get('faceindex', -1))
                task_queue.put(('draw_lines', points, Plane, faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Lines are being created"}).encode('utf-8'))
            
            elif path == '/extrude_last_sketch':
                value = float(data.get('value',1.0)) #1.0 as default
                taperangle = float(data.get('taperangle')) #0.0 as default
                task_queue.put(('extrude_last_sketch', value,taperangle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Last sketch is being extruded"}).encode('utf-8'))
                
            elif path == '/revolve':
                angle = float(data.get('angle',360)) #360 as default
                #axis = data.get('axis','X')  # 'X', 'Y', 'Z'
                task_queue.put(('revolve_profile', angle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Profile is being revolved"}).encode('utf-8'))
            elif path == '/arc':
                point1 = data.get('point1', [0,0])
                point2 = data.get('point2', [1,1])
                point3 = data.get('point3', [2,0])
                connect = bool(data.get('connect', False))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('arc', point1, point2, point3, connect, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Arc is being created"}).encode('utf-8'))
            
            elif path == '/draw_one_line':
                x1 = float(data.get('x1',0))
                y1 = float(data.get('y1',0))
                z1 = float(data.get('z1',0))
                x2 = float(data.get('x2',1))
                y2 = float(data.get('y2',1))
                z2 = float(data.get('z2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_one_line', x1, y1, z1, x2, y2, z2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Line is being created"}).encode('utf-8'))
            
            elif path == '/holes':
                points = data.get('points', [[0,0]])
                width = float(data.get('width', 1.0))
                faceindex = int(data.get('faceindex', 0))
                distance = data.get('depth', None)
                if distance is not None:
                    distance = float(distance)
                through = bool(data.get('through', False))
                task_queue.put(('holes', points, width, distance,  faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                
                self.wfile.write(json.dumps({"message": "Hole is being created"}).encode('utf-8'))

            elif path == '/create_circle':
                radius = float(data.get('radius',1.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circle', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Circle is being created"}).encode('utf-8'))

            elif path == '/extrude_thin':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                distance = float(data.get('distance',1.0)) #1.0 as default
                task_queue.put(('extrude_thin', thickness,distance))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Thin Extrude is being created"}).encode('utf-8'))

            elif path == '/select_body':
                name = str(data.get('name', ''))
                task_queue.put(('select_body', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Body is being selected"}).encode('utf-8'))

            elif path == '/select_sketch':
                name = str(data.get('name', ''))
                task_queue.put(('select_sketch', name))
       
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sketch is being selected"}).encode('utf-8'))

            elif path == '/sweep':
                # enqueue a tuple so process_task recognizes the command
                task_queue.put(('sweep',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sweep is being created"}).encode('utf-8'))
            
            elif path == '/spline':
                points = data.get('points', [])
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('spline', points, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Spline is being created"}).encode('utf-8'))

            elif path == '/cut_extrude':
                depth = float(data.get('depth',1.0)) #1.0 as default
                task_queue.put(('cut_extrude', depth))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cut Extrude is being created"}).encode('utf-8'))
            
            elif path == '/circular_pattern':
                quantity = float(data.get('quantity',))
                axis = str(data.get('axis',"X"))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circular_pattern',quantity,axis,plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Circular Pattern is being created"}).encode('utf-8'))
            
            elif path == '/offsetplane':
                offset = float(data.get('offset',0.0))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
               
                task_queue.put(('offsetplane', offset, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Offset Plane is being created"}).encode('utf-8'))

            elif path == '/loft':
                sketchcount = int(data.get('sketchcount',2))
                task_queue.put(('loft', sketchcount))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Loft is being created"}).encode('utf-8'))
            
            elif path == '/ellipsis':
                 x_center = float(data.get('x_center',0))
                 y_center = float(data.get('y_center',0))
                 z_center = float(data.get('z_center',0))
                 x_major = float(data.get('x_major',10))
                 y_major = float(data.get('y_major',0))
                 z_major = float(data.get('z_major',0))
                 x_through = float(data.get('x_through',5))
                 y_through = float(data.get('y_through',4))
                 z_through = float(data.get('z_through',0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 task_queue.put(('ellipsis', x_center, y_center, z_center,
                                  x_major, y_major, z_major, x_through, y_through, z_through, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Ellipsis is being created"}).encode('utf-8'))
                 
            elif path == '/sphere':
                radius = float(data.get('radius',5.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_sphere', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sphere is being created"}).encode('utf-8'))

            elif path == '/threaded':
                inside = bool(data.get('inside', data.get('Inside', True)))
                allsizes = int(data.get('allsizes', data.get('size_index', 0)))
                # Check both body_index and body_idx for robustness
                body_idx = int(data.get('body_index', data.get('body_idx', -1)))
                face_idx = int(data.get('face_index', data.get('face_idx', -1)))
                radius = float(data.get('radius', -1))
                
                task_queue.put(('threaded', inside, allsizes, body_idx, face_idx, radius))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Threaded feature is being created"}).encode('utf-8'))
                
            elif path == '/delete_everything':
                task_queue.put(('delete_everything',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "All bodies are being deleted"}).encode('utf-8'))
                
            elif path == '/boolean_operation':
                operation = data.get('operation', 'join')  # 'join', 'cut', 'intersect'
                target_idx = int(data.get('target_idx', 0))
                tool_idx = int(data.get('tool_idx', -1))
                task_queue.put(('boolean_operation', operation, target_idx, tool_idx))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Boolean operation is being executed"}).encode('utf-8'))
            
            elif path == '/test_connection':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Connection successful"}).encode('utf-8'))
            
            elif path == '/draw_2d_rectangle':
                x_1 = float(data.get('x_1',0))
                y_1 = float(data.get('y_1',0))
                z_1 = float(data.get('z_1',0))
                x_2 = float(data.get('x_2',1))
                y_2 = float(data.get('y_2',1))
                z_2 = float(data.get('z_2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_2d_rectangle', x_1, y_1, z_1, x_2, y_2, z_2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "2D rectangle is being created"}).encode('utf-8'))
            
            
            elif path == '/rectangular_pattern':
                 quantity_one = float(data.get('quantity_one',2))
                 distance_one = float(data.get('distance_one',5))
                 axis_one = str(data.get('axis_one',"X"))
                 quantity_two = float(data.get('quantity_two',2))
                 distance_two = float(data.get('distance_two',5))
                 axis_two = str(data.get('axis_two',"Y"))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 # Parameter-Reihenfolge: axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane
                 task_queue.put(('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Rectangular Pattern is being created"}).encode('utf-8'))
                 
            elif path == '/draw_text':
                 text = str(data.get('text',"Hello"))
                 x_1 = float(data.get('x_1',0))
                 y_1 = float(data.get('y_1',0))
                 z_1 = float(data.get('z_1',0))
                 x_2 = float(data.get('x_2',10))
                 y_2 = float(data.get('y_2',4))
                 z_2 = float(data.get('z_2',0))
                 extrusion_value = float(data.get('extrusion_value',1.0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 thickness = float(data.get('thickness',0.5))
                 faceindex = int(data.get('faceindex', -1))
                 task_queue.put(('draw_text', text, thickness, x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane, faceindex))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Text is being created"}).encode('utf-8'))
                 
            elif path == '/move_body':
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                task_queue.put(('move_body', x, y, z))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Body is being moved"}).encode('utf-8'))
            
            elif path == '/set_appearance':
                appearance_name = str(data.get('appearance_name', ''))
                if appearance_name:
                    task_queue.put(('set_appearance', appearance_name))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Appearance {appearance_name} is being set"}).encode('utf-8'))
                else:
                    self.send_error(400, "Missing appearance_name")
            elif path == '/run_script':
                code = data.get('code', '')
                if code:
                    task_queue.put(('run_script', code))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": "Script is being executed"}).encode('utf-8'))
                else:
                    self.send_error(400, "Missing code")
            
            elif path == '/add_snap_fit_joint':
                f_idx = int(data.get('female_body_idx', 0))
                fx = float(data.get('female_x', 0))
                fy = float(data.get('female_y', 0))
                fz = float(data.get('female_z', 0))
                m_idx = int(data.get('male_body_idx', 1))
                mx = float(data.get('male_x', 0))
                my = float(data.get('male_y', 0))
                mz = float(data.get('male_z', 0))
                radius = float(data.get('radius', 0.25))
                
                task_queue.put(('add_snap_fit_joint', f_idx, fx, fy, fz, m_idx, mx, my, mz, radius))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Snap-fit joint is being applied"}).encode('utf-8'))
            
            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

def run_server():
    global httpd
    server_address = ('localhost',5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


def run(context):
    global app, ui, design, handlers, stopFlag, customEvent
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Defer design initialization until it's actually needed in the event handler
        design = None
        try:
            if app.activeProduct:
                design = adsk.fusion.Design.cast(app.activeProduct)
        except:
            pass

        # Initial snapshot (if design is available)
        global ModelParameterSnapshot
        if design:
            ModelParameterSnapshot = get_model_parameters(design)
        else:
            ModelParameterSnapshot = []

        # Register custom event
        customEvent = app.registerCustomEvent(myCustomEvent)
        onTaskEvent = TaskEventHandler()
        customEvent.add(onTaskEvent)
        handlers.append(onTaskEvent)

        # Start task thread
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.daemon = True
        taskThread.start()

        print(f"Fusion HTTP Add-In started! Port 5000. (Version 2.0)\nParameters loaded: {len(ModelParameterSnapshot)} model parameters")

        # Start HTTP server
        threading.Thread(target=run_server, daemon=True).start()

    except:
        try:
            print('Error in Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass




def stop(context):
    global stopFlag, httpd, task_queue, handlers, app, customEvent
    
    # Stop the task thread
    if stopFlag:
        stopFlag.set()

    # Clean up event handlers
    for handler in handlers:
        try:
            if customEvent:
                customEvent.remove(handler)
        except:
            pass
    
    handlers.clear()

    # Clear the queue without processing (avoid freezing)
    while not task_queue.empty():
        try:
            task_queue.get_nowait() 
            if task_queue.empty(): 
                break
        except:
            break

    # Stop HTTP server
    if httpd:
        try:
            httpd.shutdown()
        except:
            pass

  
    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except:
            pass
        httpd = None
    try:
        app = adsk.core.Application.get()
        if app:
            ui = app.userInterface
            if ui:
                print("Fusion HTTP Add-In stopped")
    except:
        pass
