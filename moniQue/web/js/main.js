import {
    PerspectiveCamera,
    Color,
    Scene,
    WebGLRenderer,
    AxesHelper,
    Mesh,
    MeshStandardMaterial,
    HemisphereLight,
    DirectionalLight,
    Group,
    TextureLoader,
    SRGBColorSpace
    } from 'three';

import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {PLYLoader} from 'three/addons/loaders/PLYLoader.js'

// Get a reference to the container element that will hold our scene
const container = document.querySelector('#scene-container');

// create a Scene
const scene = new Scene();
scene.add(new AxesHelper(10))


// const hem_light = new HemisphereLight( 0xffffbb, 0x080820, 1 );
// scene.add(hem_light)
const dir_light = new DirectionalLight( 0xffffff, 2);
scene.add(dir_light)

// Set the background color
scene.background = new Color('skyblue');

// Create a camera
const fov = 45; // AKA Field of View
const aspect = container.clientWidth / container.clientHeight;
const near = 1; // the near clipping plane
const far = 100000; // the far clipping plane

const camera = new PerspectiveCamera(fov, aspect, near, far);
camera.position.z = 40

const renderer = new WebGLRenderer()
renderer.setSize(container.clientWidth, container.clientHeight)
renderer.setPixelRatio(window.devicePixelRatio);
container.append(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement)
controls.enableDamping = true

const material = new MeshStandardMaterial()

const ply_loader = new PLYLoader()
const tex_loader = new TextureLoader();

const terrain = new Group();


let pix = 0
const ply_names = ["0_0", "0_1", "0_2", "1_0", "1_1", "1_2", "2_0", "2_1", "2_2"]

//recursive loading of terrain tiles; otherwise all tiles are loaded asynchronsly which is quite slow
function load_ply() {

    if (pix > ply_names.length - 1) {
        terrain.position.x = -621373.0
        terrain.position.y = -5153392.0
        terrain.position.z = -2323.882
        scene.add(terrain)
        return
    }

    ply_loader.load('./data/mesh/' + ply_names[pix] + '.ply',
        function (geometry) {
            geometry.computeVertexNormals()        
            const mesh = new Mesh(geometry, material)
            mesh.name = ply_names[pix]
            terrain.add(mesh)
            
            if (pix == 0) {
                load_tex()
            }
            pix ++
            load_ply()
        },
        (xhr) => {
            console.log((xhr.loaded / xhr.total) * 100 + '% loaded')
        },
        (error) => {
            console.log(error)
        }
    )
}

load_ply()

function load_tex() {
    // load a resource
    tex_loader.load(
        // resource URL
        './data/op/' + ply_names[0] + '.jpg',

        // onLoad callback
        function ( texture ) {
            
            texture.colorSpace = SRGBColorSpace;
            let tile_mat = new MeshStandardMaterial({map:texture})
            
            let curr_tile = terrain.getObjectByName(ply_names[0])
            
           var uvAttribute = curr_tile.attributes.uv;
                    
            for ( var i = 0; i < uvAttribute.count; i ++ ) {
                    
                var u = uvAttribute.getX( i );
                var v = uvAttribute.getY( i );
                        
                // do something with uv

                // write values back to attribute
                        
                uvAttribute.setXY( i, u, v );
                    
            }

            curr_tile.material = tile_mat
        },

        // onProgress callback currently not supported
        undefined,

        // onError callback
        function ( err ) {
            console.error( 'An error happened.' );
        }
    );
    }



function animate() {
    requestAnimationFrame(animate)

    controls.update()

    render()
}

function render() {
    renderer.render(scene, camera)
    requestAnimationFrame(render);

}

animate()