// Face landmarks and person cutouts with Apple's Vision framework (no downloads).
// vision landmarks img...           -> one JSON line per image (largest face, pixel coords, top-left origin)
// vision mask person|fg in out.png  -> 8-bit mask at the image's own size
import Foundation
import Vision
import CoreImage
import ImageIO
let a = Array(CommandLine.arguments.dropFirst())
func load(_ p: String) -> CGImage? {
  guard let s = CGImageSourceCreateWithURL(URL(fileURLWithPath: p) as CFURL, nil) else { return nil }
  return CGImageSourceCreateImageAtIndex(s, 0, nil)
}
if a.first == "landmarks" {
  for p in a.dropFirst() {
    guard let cg = load(p) else { print("{\"file\":\"\(p)\",\"faces\":0}"); continue }
    let W = Double(cg.width), H = Double(cg.height)
    let r = VNDetectFaceLandmarksRequest(); r.constellation = .constellation76Points
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([r])
    let fs = (r.results ?? []).sorted { $0.boundingBox.width > $1.boundingBox.width }
    guard let f = fs.first, let L = f.landmarks else { print("{\"file\":\"\(p)\",\"faces\":0}"); continue }
    func pts(_ x: VNFaceLandmarkRegion2D?) -> [[Double]] {
      (x?.pointsInImage(imageSize: CGSize(width: W, height: H)) ?? []).map { [Double($0.x), H - Double($0.y)] }
    }
    let big = fs.filter { $0.boundingBox.width > f.boundingBox.width * 0.35 }.count
    let d: [String: Any] = ["file": p, "w": W, "h": H, "faces": big, "all": pts(L.allPoints), "leftEye": pts(L.leftEye),
      "rightEye": pts(L.rightEye), "nose": pts(L.nose), "noseCrest": pts(L.noseCrest), "outerLips": pts(L.outerLips), "innerLips": pts(L.innerLips),
      "leftBrow": pts(L.leftEyebrow), "rightBrow": pts(L.rightEyebrow), "contour": pts(L.faceContour)]
    print(String(data: try! JSONSerialization.data(withJSONObject: d), encoding: .utf8)!)
  }
} else if a.first == "mask", a.count == 4, let cg = load(a[2]) {
  let h = VNImageRequestHandler(cgImage: cg, options: [:]); var pb: CVPixelBuffer
  if a[1] == "person" {
    let r = VNGeneratePersonSegmentationRequest(); r.qualityLevel = .accurate; r.outputPixelFormat = kCVPixelFormatType_OneComponent8
    try! h.perform([r]); pb = r.results!.first!.pixelBuffer
  } else {
    let r = VNGenerateForegroundInstanceMaskRequest(); try! h.perform([r])
    guard let o = r.results?.first else { FileHandle.standardError.write("no foreground found\n".data(using: .utf8)!); exit(2) }
    pb = try! o.generateScaledMaskForImage(forInstances: o.allInstances, from: h)
  }
  let ci = CIImage(cvPixelBuffer: pb).transformed(by: CGAffineTransform(scaleX: Double(cg.width) / Double(CVPixelBufferGetWidth(pb)), y: Double(cg.height) / Double(CVPixelBufferGetHeight(pb))))
  let out = CIContext().createCGImage(ci, from: CGRect(x: 0, y: 0, width: cg.width, height: cg.height), format: .L8, colorSpace: CGColorSpace(name: CGColorSpace.linearGray)!)!
  let dst = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[3]) as CFURL, "public.png" as CFString, 1, nil)!
  CGImageDestinationAddImage(dst, out, nil); CGImageDestinationFinalize(dst)
} else { print("usage: vision landmarks img... | vision mask person|fg in out.png"); exit(1) }
